"""
push-to-feishu.py

Takes a record_id, markdown content string, doc title, and persona name.
Does the following in order:
  1. Creates a new Feishu Doc inside the configured output folder.
  2. Generates a cover image and saves it to output/covers/<title>.png.
  3. Writes the markdown content into the doc as structured blocks.
  4. Updates the Bitable row:
       - Sets "Blog Draft" to the new doc URL
       - Sets "Status" to "Drafting"
       - Sets "Target Account" to the persona name

Usage (programmatic — called from the pipeline, not directly):
    from push_to_feishu import push_article
    doc_url = push_article(record_id, markdown_content, title, persona)

Cover image generation requires openrouter_api_key in config/feishu-config.json.
Pass generate_cover=False to skip image generation.
"""

import json
import os
import re
import sys
import time

import requests

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../config/feishu-config.json")
GENERATE_IMAGE_SCRIPT = os.path.join(os.path.dirname(__file__), "generate-image.py")

# Feishu Docs block type constants
BLOCK_TEXT = 2
BLOCK_H1 = 3
BLOCK_H2 = 4
BLOCK_H3 = 5
BLOCK_CODE = 12
BLOCK_BULLET = 15
BLOCK_ORDERED = 17

# Feishu code block language: 1 = PlainText, 23 = Python, 49 = Go, etc.
LANG_MAP = {
    "python": 23, "py": 23,
    "go": 49, "golang": 49,
    "javascript": 4, "js": 4,
    "typescript": 4, "ts": 4,
    "bash": 2, "sh": 2, "shell": 2,
    "sql": 27,
    "json": 13,
    "yaml": 35, "yml": 35,
}


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def get_tenant_access_token(config):
    resp = requests.post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": config["app_id"], "app_secret": config["app_secret"]},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"Failed to get access token: {data}")
    return data["tenant_access_token"]


# ---------------------------------------------------------------------------
# Markdown → Feishu blocks
# ---------------------------------------------------------------------------

def parse_inline(text: str) -> list:
    """
    Convert inline markdown (links, bold, inline code) into Feishu text_run
    element objects. Handles [text](url), **bold**, and `code`.
    """
    elements = []
    # Combined pattern: links, bold, inline code
    pattern = re.compile(
        r"\[(?P<link_text>[^\]]+)\]\((?P<link_url>[^)]+)\)"  # [text](url)
        r"|\*\*(?P<bold>[^*]+)\*\*"                           # **bold**
        r"|`(?P<code>[^`]+)`"                                 # `code`
    )
    last_end = 0

    for match in pattern.finditer(text):
        # Plain text before this match
        if match.start() > last_end:
            elements.append({"text_run": {"content": text[last_end:match.start()]}})

        if match.group("link_text"):
            elements.append({
                "text_run": {
                    "content": match.group("link_text"),
                    "text_element_style": {
                        "link": {"url": match.group("link_url")}
                    },
                }
            })
        elif match.group("bold"):
            elements.append({
                "text_run": {
                    "content": match.group("bold"),
                    "text_element_style": {"bold": True},
                }
            })
        elif match.group("code"):
            elements.append({
                "text_run": {
                    "content": match.group("code"),
                    "text_element_style": {"inline_code": True},
                }
            })

        last_end = match.end()

    # Trailing plain text
    if last_end < len(text):
        elements.append({"text_run": {"content": text[last_end:]}})

    return elements or [{"text_run": {"content": text}}]


def make_block(block_type: int, key: str, elements: list, extra_style: dict = None) -> dict:
    block = {
        "block_type": block_type,
        key: {
            "elements": elements,
            "style": extra_style or {},
        },
    }
    return block


def make_code_block(code: str, lang: str) -> dict:
    # The Feishu Create Block API does not support code blocks (type 12).
    # Workaround: render code as a text block with inline_code styling.
    return {
        "block_type": BLOCK_TEXT,
        "text": {
            "elements": [
                {"text_run": {"content": code, "text_element_style": {"inline_code": True}}}
            ],
            "style": {},
        },
    }


def markdown_to_blocks(md_content: str) -> list:
    """Convert a markdown string to a list of Feishu document block definitions."""
    blocks = []
    lines = md_content.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        # Fenced code block
        if line.startswith("```"):
            lang = line[3:].strip() or "plaintext"
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            blocks.append(make_code_block("\n".join(code_lines), lang))

        # Heading 1
        elif re.match(r"^# [^#]", line):
            text = line[2:].strip()
            blocks.append(make_block(BLOCK_H1, "heading1", parse_inline(text)))

        # Heading 2
        elif re.match(r"^## [^#]", line):
            text = line[3:].strip()
            blocks.append(make_block(BLOCK_H2, "heading2", parse_inline(text)))

        # Heading 3
        elif re.match(r"^### ", line):
            text = line[4:].strip()
            blocks.append(make_block(BLOCK_H3, "heading3", parse_inline(text)))

        # Bullet list item — render as text with bullet prefix (API doesn't accept block_type 15)
        elif re.match(r"^[-*] ", line):
            text = line[2:].strip()
            elements = parse_inline(text)
            # Prepend bullet symbol as plain text
            elements.insert(0, {"text_run": {"content": "• "}})
            blocks.append(make_block(BLOCK_TEXT, "text", elements))

        # Numbered list item — render as text with number prefix
        elif re.match(r"^\d+\. ", line):
            num = re.match(r"^(\d+)\. ", line).group(1)
            text = re.sub(r"^\d+\. ", "", line).strip()
            elements = parse_inline(text)
            elements.insert(0, {"text_run": {"content": f"{num}. "}})
            blocks.append(make_block(BLOCK_TEXT, "text", elements))

        # Empty line: skip
        elif line.strip() == "":
            pass

        # Horizontal rule: skip
        elif re.match(r"^[-*_]{3,}$", line.strip()):
            pass

        # Regular paragraph
        else:
            blocks.append(make_block(BLOCK_TEXT, "text", parse_inline(line)))

        i += 1

    return blocks


# ---------------------------------------------------------------------------
# Feishu API calls
# ---------------------------------------------------------------------------

def create_feishu_doc(token: str, folder_token: str, title: str) -> str:
    """
    Create a new Feishu Doc in the specified folder.

    Returns:
        str: The new document's document_id.
    """
    resp = requests.post(
        "https://open.feishu.cn/open-apis/docx/v1/documents",
        headers={"Authorization": f"Bearer {token}"},
        json={"folder_token": folder_token, "title": title},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"Failed to create doc: {data}")
    return data["data"]["document"]["document_id"]


def write_blocks_to_doc(token: str, document_id: str, blocks: list):
    """
    Write blocks to the root of a Feishu Doc, in batches of 50.
    The root block_id equals the document_id.
    """
    url = (
        f"https://open.feishu.cn/open-apis/docx/v1"
        f"/documents/{document_id}/blocks/{document_id}/children"
    )
    headers = {"Authorization": f"Bearer {token}"}
    batch_size = 50

    for start in range(0, len(blocks), batch_size):
        batch = blocks[start : start + batch_size]
        resp = requests.post(
            url,
            headers=headers,
            json={"children": batch, "index": start},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise RuntimeError(f"Failed to write blocks (batch {start}): {data}")
        # Brief pause to avoid rate limiting on large docs
        if start + batch_size < len(blocks):
            time.sleep(0.3)


def grant_org_edit_access(token: str, document_id: str):
    """
    Set the doc's link-share permission to 'tenant_editable' so everyone
    in the Zilliz org can edit without an explicit invite.
    """
    resp = requests.patch(
        f"https://open.feishu.cn/open-apis/drive/v1/permissions/{document_id}/public?type=docx",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "external_access_entity": "open",
            "security_entity": "anyone_can_view",
            "comment_entity": "anyone_can_view",
            "share_entity": "anyone",
            "link_share_entity": "tenant_editable",
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"Failed to set doc permissions: {data}")


def update_bitable_record(
    token: str,
    config: dict,
    record_id: str,
    doc_url: str,
    persona: str,
):
    """
    Update the Bitable row: set Blog Draft URL, Status → Drafting,
    Target Account → persona name.
    """
    app_token = config["bitable_app_token"]
    table_id = config["bitable_table_id"]
    url = (
        f"https://open.feishu.cn/open-apis/bitable/v1"
        f"/apps/{app_token}/tables/{table_id}/records/{record_id}"
    )
    payload = {
        "fields": {
            "Blog Draft": doc_url,
            "Status": "Drafting",
            "Target Account": persona,
        }
    }
    resp = requests.put(
        url,
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"Failed to update Bitable record: {data}")


# ---------------------------------------------------------------------------
# Cover image (saved locally)
# ---------------------------------------------------------------------------

def generate_and_save_cover(persona: str, article_title: str):
    """
    Generate a cover image via OpenRouter and save it to output/covers/<title>.png.
    Returns the local file path, or None on failure.
    """
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("generate_image", GENERATE_IMAGE_SCRIPT)
        gen_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gen_mod)
        return gen_mod.generate_cover_image(persona, article_title)
    except Exception as e:
        print(f"  Warning: cover image generation failed ({e}). Continuing without cover.")
        return None


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def push_article(
    record_id: str,
    markdown_content: str,
    doc_title: str,
    persona: str,
    generate_cover: bool = True,
) -> str:
    """
    Full pipeline step: create Feishu Doc, write content, update Bitable row.

    Args:
        record_id:        Bitable record ID of the source row.
        markdown_content: Rewritten article in markdown format.
        doc_title:        Title for the new Feishu Doc.
        persona:          One of "Alex Chen", "Priya Singh", "Carlos Martínez".
        generate_cover:   If True (default), generate a cover image and save it
                          to output/covers/<title>.png. Requires
                          openrouter_api_key in config/feishu-config.json.

    Returns:
        str: The URL of the created Feishu Doc.
    """
    config = load_config()
    token = get_tenant_access_token(config)
    folder_token = config["output_folder_token"]
    base_url = config.get("base_url", "https://bytedance.feishu.cn").rstrip("/")

    print(f"  Creating Feishu Doc: {doc_title!r}")
    document_id = create_feishu_doc(token, folder_token, doc_title)
    doc_url = f"{base_url}/docx/{document_id}"
    print(f"  Doc created: {doc_url}")

    # Build content blocks
    blocks = markdown_to_blocks(markdown_content)

    # Generate and save cover image locally
    if generate_cover:
        print("  Generating cover image...")
        cover_path = generate_and_save_cover(persona, doc_title)
        if cover_path:
            print(f"  Cover image saved: {cover_path}")

    print("  Writing content blocks...")
    write_blocks_to_doc(token, document_id, blocks)
    print(f"  Wrote {len(blocks)} blocks.")

    print("  Granting org-wide edit access...")
    grant_org_edit_access(token, document_id)
    print("  Permissions set (tenant_editable).")

    print(f"  Updating Bitable record {record_id}...")
    update_bitable_record(token, config, record_id, doc_url, persona)
    print("  Bitable row updated (Status → Drafting).")

    return doc_url


if __name__ == "__main__":
    # Quick smoke-test: python push-to-feishu.py <record_id> <md_file> "<title>" "<persona>"
    if len(sys.argv) != 5:
        print(
            "Usage: python push-to-feishu.py "
            "<record_id> <markdown_file> <title> <persona>"
        )
        sys.exit(1)

    rid, md_path, title, persona_name = sys.argv[1:]
    with open(md_path) as f:
        content = f.read()

    url = push_article(rid, content, title, persona_name)
    print(f"\nDone. Doc URL: {url}")
