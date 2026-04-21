---
name: Cover image generation pipeline
description: How cover images are generated, sized, and saved — OpenRouter + Pillow, local only, not in Feishu
type: project
---

## How it works

1. `push_article(..., generate_cover=True)` calls `generate_and_save_cover(persona, title)` in `push-to-feishu.py`
2. That dynamically loads `scripts/generate-image.py` via importlib
3. OpenRouter (`google/gemini-2.5-flash-image`) generates the image via chat completions
4. Pillow center-crops and resizes to exactly **1280×1024 (10:8 ratio)**
5. Saved to `output/covers/<sanitized_title>.png` (gitignored)

## OpenRouter image API

- Endpoint: `POST https://openrouter.ai/api/v1/chat/completions`
- `/images/generations` endpoint does **not** exist on OpenRouter — returns 404
- Available image models: `google/gemini-2.5-flash-image`, `google/gemini-3.1-flash-image-preview`, `openai/gpt-5-image-mini`, `openai/gpt-5-image`
- FLUX models (`black-forest-labs/flux-*`) are **not available** on this account
- Models always output 1024×1024 regardless of prompt — Pillow post-processing is mandatory for correct size
- Response: `data["choices"][0]["message"]["images"][0]["image_url"]["url"]` (base64 data-URI)

## Style files

`cover-image/alex-chen.md`, `cover-image/priya-singh.md`, `cover-image/carlos-martinez.md`
Each has a persona color palette + prompt template with `[TOPIC]` placeholder. All specify 10:8 landscape format.

## Requirements

- `openrouter_api_key` in `config/feishu-config.json`
- `Pillow` installed (`pip install Pillow`)
- Images are **not** embedded in Feishu docs (API limitation — see `feishu_api.md`)
