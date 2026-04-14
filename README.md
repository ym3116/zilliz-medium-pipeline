# Zilliz KOC Medium Blog Pipeline

An automated pipeline for rewriting Medium articles in the voice of Zilliz KOC (Key Opinion Creator) personas, inserting backlinks, and publishing the results to Feishu Docs.

---

## Pipeline Overview

```
Feishu Sheet (article URLs)
        ↓
  Filter unsuitable articles
        ↓
  Classify → assign persona (Alex / Priya / Carlos)
        ↓
  Rewrite in persona voice + insert backlinks
        ↓
  Push rewritten doc to Feishu Docs
        ↓
  Write doc URL back to Feishu Sheet
```

---

## Personas

| Persona | Focus |
|---|---|
| **Alex Chen** | Engineering deep-dives, benchmarks, system architecture |
| **Priya Singh** | Applied AI, RAG pipelines, LLM tutorials |
| **Carlos Martínez** | Enterprise strategy, business value, market trends |

Full profiles and rewrite prompts are in the `personas/` directory.

---

## Setup

1. Copy credentials into `config/feishu-config.json` (never commit this file).
2. Install dependencies: `pip install -r requirements.txt` *(coming soon)*
3. Run the pipeline scripts in order:
   - `python scripts/fetch-articles.py` — pull unprocessed rows
   - `python scripts/classify.py <url>` — suggest a persona
   - *(rewrite step — Claude-assisted)*
   - `python scripts/push-to-feishu.py <draft.md> <row_index>` — publish and record

---

## Configuration

| File | Purpose |
|---|---|
| `config/feishu-config.json` | Feishu API credentials (gitignored) |
| `config/link-rules.md` | Keyword → backlink URL mapping |

---

## Output

Rewritten markdown drafts are saved locally to `output/drafts/` before being pushed to Feishu.
