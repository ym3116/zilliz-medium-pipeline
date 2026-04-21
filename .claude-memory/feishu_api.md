---
name: Feishu API quirks and limitations
description: All known Feishu docx/Bitable API limitations for this pipeline — block types, image embedding, field formats
type: feedback
---

## Docx block types

**Work:** text (2), heading1 (3), heading2 (4), heading3 (5)

**Fail with code 1770001 — use these workarounds instead:**
- code (12) → text block (2) with `inline_code` styling on the text_run
- bullet list (15) → text block with `"• "` prepended
- ordered list (17) → text block with `"N. "` prepended
- image (27) → silently accepted but **img_token is always dropped** (see below)

All conversions are handled in `markdown_to_blocks()` in `push-to-feishu.py`. Never add block types 12, 15, or 17.

## Image blocks are broken for bot tokens

`block_type=27` image blocks always store `token: ""` even when a valid `img_token` is passed. The block creation returns code=0 but Feishu never persists the token. PATCH also fails (1770001). This is a missing scope on the bot app — would require OAuth user_access_token or Feishu admin enabling the scope. **Do not attempt image embedding via the API.** Save cover images locally instead.

## Bitable field formats

- **"Blog Draft"** field: plain string (the doc URL). Do NOT send a structured `[{"text": ..., "link": ...}]` object.
- **"Source Link"** field: returns as a dict `{"link": "https://..."}` — extract with `field_value["link"]`.
- **base_url:** config has no `base_url` set → doc URLs default to `bytedance.feishu.cn`. User's actual tenant is `zilliverse.feishu.cn`. Both work; to fix add `"base_url": "https://zilliverse.feishu.cn"` to `feishu-config.json`.
