---
name: Feishu doc writing quirks
description: What works and fails when writing content blocks to Feishu Docs via the API — code blocks fail, text+callout blocks work
type: feedback
---
Code blocks (block_type 12) ALWAYS fail with "invalid param" (code 1770001) via the Feishu Create Block API. This happens regardless of language setting, style options, or content length.

**Why:** Likely a Feishu API limitation — the Create Document Block Children endpoint does not support the code block type.

**How to apply:**
- `push-to-feishu.py` has been patched (2026-04-17) to render code as text blocks with `inline_code` styling:
  ```python
  {"block_type": 2, "text": {"elements": [{"text_run": {"content": code, "text_element_style": {"inline_code": True}}}], "style": {}}}
  ```
- Callout blocks (type 19) also work and can be used as an alternative visual container.
- All other block types work: text (2), heading1 (3), heading2 (4), heading3 (5), bullet (15), ordered (16).
- The Bitable "Blog Draft" field is a **multiline text** field (plain string), NOT a URL/link field. Send a plain string, not `[{"text": ..., "link": ...}]`. This was fixed in `push-to-feishu.py` on 2026-04-17.
