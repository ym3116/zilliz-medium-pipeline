"""
scripts/generate-image.py

Generates a cover image for an article using OpenRouter (google/gemini-2.5-flash-image)
and saves it locally to output/covers/<sanitized_title>.png.

Configuration:
    Set "openrouter_api_key" in config/feishu-config.json.

Usage (programmatic — called from push-to-feishu.py):
    spec = importlib.util.spec_from_file_location("generate_image", path)
    mod  = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    local_path = mod.generate_cover_image(persona, article_title)

CLI smoke test:
    python scripts/generate-image.py "Priya Singh" "RAG pipeline article title"
"""

import base64
import io
import json
import os
import re
import sys

import requests
from PIL import Image

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPTS_DIR = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(SCRIPTS_DIR, "../config/feishu-config.json")
STYLE_DIR   = os.path.join(SCRIPTS_DIR, "../cover-image")
OUTPUT_DIR  = os.path.join(SCRIPTS_DIR, "../output/covers")

# Image generation model via OpenRouter chat completions.
# google/gemini-2.5-flash-image produces high-quality images and respects
# aspect ratio instructions in the prompt (10:8 / 5:4 landscape).
IMAGE_MODEL = "google/gemini-2.5-flash-image"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

PERSONA_STYLE_FILES = {
    "Alex Chen":       "alex-chen.md",
    "Priya Singh":     "priya-singh.md",
    "Carlos Martínez": "carlos-martinez.md",
}


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return json.load(f)


def get_openrouter_key(config: dict) -> str:
    key = config.get("openrouter_api_key", "")
    if not key:
        raise EnvironmentError(
            "openrouter_api_key is missing from config/feishu-config.json. "
            "Add your OpenRouter API key there to enable cover image generation."
        )
    return key


# ---------------------------------------------------------------------------
# Prompt building
# ---------------------------------------------------------------------------

def load_style(persona: str) -> str:
    filename = PERSONA_STYLE_FILES.get(persona)
    if not filename:
        raise ValueError(f"Unknown persona: {persona!r}")
    with open(os.path.join(STYLE_DIR, filename)) as f:
        return f.read()


def build_prompt(persona: str, article_title: str) -> str:
    """Extract the prompt template from the persona style file and fill in the topic."""
    style = load_style(persona)

    match = re.search(r"```\n(.*?)```", style, re.DOTALL)
    if match:
        template = match.group(1).strip()
    else:
        template = (
            "A 10:8 comic-style cover illustration for a technical article about [TOPIC]. "
            "High-tech comic art, rich visual elements. No text, no logos, no brand names."
        )

    topic = re.sub(r"[^\w\s,.:+/-]", "", article_title).strip()[:120]
    prompt = template.replace("[TOPIC]", topic)
    prompt += " Generate as a landscape image with 10:8 (5:4) aspect ratio. High quality digital illustration, detailed, vibrant. No watermarks, no text overlays."
    return prompt


# ---------------------------------------------------------------------------
# Image generation via OpenRouter
# ---------------------------------------------------------------------------

def generate_image_bytes(prompt: str, api_key: str) -> bytes:
    """
    Call IMAGE_MODEL via OpenRouter chat completions.
    Aspect ratio (10:8 / 5:4) is enforced via the prompt.
    Returns raw image bytes (PNG or JPEG).
    """
    resp = requests.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": IMAGE_MODEL,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=180,
    )
    resp.raise_for_status()
    data = resp.json()

    try:
        image_entry = data["choices"][0]["message"]["images"][0]
        raw = image_entry["image_url"]["url"]
    except (KeyError, IndexError, TypeError) as e:
        raise RuntimeError(
            f"Unexpected OpenRouter image response structure: {e}\n"
            f"Response keys: {list(data.get('choices', [{}])[0].get('message', {}).keys())}"
        )

    # Strip data-URI prefix if present
    if raw.startswith("data:"):
        _, b64 = raw.split(",", 1)
    else:
        b64 = raw

    return base64.b64decode(b64)


# ---------------------------------------------------------------------------
# Resize to exact 10:8 (1280×1024)
# ---------------------------------------------------------------------------

COVER_WIDTH  = 1280
COVER_HEIGHT = 1024  # 10:8 = 5:4 ratio

def enforce_aspect_ratio(image_bytes: bytes) -> bytes:
    """
    Center-crop the image to 10:8 (5:4) ratio, then resize to
    exactly 1280×1024. Works regardless of what size the model outputs.
    Returns PNG bytes.
    """
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    w, h = img.size
    target_ratio = COVER_WIDTH / COVER_HEIGHT  # 1.25

    current_ratio = w / h
    if current_ratio < target_ratio:
        # Too tall — crop height, keep full width
        new_h = int(w / target_ratio)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))
    elif current_ratio > target_ratio:
        # Too wide — crop width, keep full height
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))

    img = img.resize((COVER_WIDTH, COVER_HEIGHT), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Local save
# ---------------------------------------------------------------------------

def sanitize_filename(title: str) -> str:
    """Convert article title to a safe filename (no path separators, no special chars)."""
    name = re.sub(r'[\\/:*?"<>|]', "", title)   # remove filesystem-illegal chars
    name = re.sub(r"\s+", "_", name.strip())      # spaces → underscores
    return name[:200]                              # cap length


def save_image_locally(image_bytes: bytes, article_title: str) -> str:
    """
    Save image bytes to output/covers/<title>.png.
    Returns the absolute path of the saved file.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = sanitize_filename(article_title) + ".png"
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "wb") as f:
        f.write(image_bytes)
    return os.path.abspath(path)


# ---------------------------------------------------------------------------
# Main entry point (called from push-to-feishu.py)
# ---------------------------------------------------------------------------

def generate_cover_image(
    persona: str,
    article_title: str,
) -> str:
    """
    Full pipeline:
      1. Build persona-specific prompt from article title.
      2. Generate image via OpenRouter (google/gemini-2.5-flash-image).
      3. Save to output/covers/<title>.png.
      4. Return the local file path.
    """
    config = load_config()
    api_key = get_openrouter_key(config)

    print(f"  Building image prompt for: {persona}")
    prompt = build_prompt(persona, article_title)
    print(f"  Prompt (first 120 chars): {prompt[:120]}...")

    print(f"  Generating cover image via OpenRouter ({IMAGE_MODEL})...")
    image_bytes = generate_image_bytes(prompt, api_key)
    print(f"  Image generated ({len(image_bytes) // 1024} KB).")

    print(f"  Resizing to {COVER_WIDTH}×{COVER_HEIGHT} (10:8)...")
    image_bytes = enforce_aspect_ratio(image_bytes)
    print(f"  Resized ({len(image_bytes) // 1024} KB).")

    local_path = save_image_locally(image_bytes, article_title)
    print(f"  Saved locally: {local_path}")

    return local_path


# ---------------------------------------------------------------------------
# CLI: python scripts/generate-image.py "Priya Singh" "Article Title"
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    persona    = sys.argv[1] if len(sys.argv) > 1 else "Priya Singh"
    title      = sys.argv[2] if len(sys.argv) > 2 else "Test Article"

    print(f"Generating cover for: {persona!r} | {title!r}")
    path = generate_cover_image(persona, title)
    print(f"\nDone. Saved to: {path}")
