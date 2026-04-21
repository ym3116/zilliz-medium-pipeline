# Zilliz KOC Medium Blog Pipeline — Claude Instructions

## Trigger Phrase

When the user says **"process N articles"** or **"process next N TODO rows"**, execute the full pipeline below for the first N unprocessed rows.

---

## Full Pipeline

### Step 1 — Fetch TODO Rows
Run `scripts/fetch-articles.py` to pull all rows where `Status = TODO` from the Bitable table.
Take only the **first N rows** returned.

### Step 2 — Classify Personas
Run `scripts/classify.py` on those N rows.
- Assign each article to exactly one of: **Alex Chen**, **Priya Singh**, **Carlos Martínez**.
- **Never assign James** or any other persona not in that list.
- Balance assignments: check existing counts in the full table before deciding, so no persona is over-represented.

### Step 3 — For Each Row, Rewrite the Article

Do all of the following for every row:

**3a. Fetch article content**
Fetch the full article text from `source_link`. Use a browser-like User-Agent header. Strip navigation, headers, footers, and ads. Keep the body text, headings, and code snippets.

**3b. Load persona file**
Read `personas/<persona>.md` matching the assigned persona:
- Alex Chen → `personas/alex-chen.md`
- Priya Singh → `personas/priya-singh.md`
- Carlos Martínez → `personas/carlos-martinez.md`

**3c. Load backlink rules**
Read `config/link-rules.md` for the keyword → URL mapping table.

**3d. Rewrite the article**
Rewrite the article **completely** in the persona's voice, following the instructions in their persona file. Requirements:
- **Length:** 1000–2000 words.
- **Voice:** Must sound genuinely like the persona — not like a summary, translation, or generic rewrite.
- **Code:** Include relevant code snippets where appropriate (Python, Go, SQL, etc.). Use real, working code.
- **Technical accuracy:** Stay grounded in the original article's facts. Do not invent benchmarks or results.
- **Structure:** Use headings, bullet points, and numbered lists as the persona naturally would.
- **No hype:** Avoid marketing language. The persona never sounds promotional.

**3e. Insert backlinks**
After rewriting, scan the text for keywords from `config/link-rules.md`.
- Hyperlink **each keyword at most once** (first occurrence only).
- Append `?utm_campaign=mediumkoc` to every URL.
- Do **not** link inside code blocks or headings.
- Use standard markdown link syntax: `[keyword](url?utm_campaign=mediumkoc)`.

**3f. Use the Repurposed Title as doc title**
The `repurposed_title` field from the Bitable row is the doc title. Use it exactly as-is.

### Step 4 — Push to Feishu
Call `scripts/push-to-feishu.py` (via `push_article()`) with:
- `record_id` — from the Bitable row
- `markdown_content` — the rewritten article
- `doc_title` — the `repurposed_title` value
- `persona` — the assigned persona name

This will:
- Create a new Feishu Doc in folder `OmH3fQT3QlEx1ldBuDUctQlrnId` (SEO Reposts)
- Write the markdown content as structured blocks
- Update the Bitable row: `Blog Draft` → doc URL, `Status` → `Drafting`, `Target Account` → persona name

### Step 5 — Print Summary
After all N rows are processed, print a summary:

```
Processed 3 articles:
  1. [record_id] "Doc Title" → Alex Chen
     Doc URL: https://...feishu.cn/docx/...
  2. [record_id] "Doc Title" → Priya Singh
     Doc URL: https://...
  3. [record_id] "Doc Title" → Carlos Martínez
     Doc URL: https://...
```

---

## Persona Assignment Rules

| Persona | Signals |
|---|---|
| **Alex Chen** | Engineering deep-dives, database internals, benchmarks, indexing algorithms, C++/Go, performance tuning |
| **Priya Singh** | RAG pipelines, LLM use cases, LangChain/LlamaIndex, tutorials, applied AI, embedding workflows |
| **Carlos Martínez** | Kafka/Kubernetes/ETL infrastructure, DevOps, enterprise deployments, data platform architecture |

---

## Backlink Rules Summary

All URLs from `config/link-rules.md`. Add `?utm_campaign=mediumkoc`. Link first occurrence only. Never link inside code blocks or headings.

---

## File Reference

| File | Role |
|---|---|
| `config/feishu-config.json` | Feishu API credentials (gitignored) |
| `config/link-rules.md` | Keyword → backlink URL table |
| `personas/alex-chen.md` | Alex's profile, style, and rewrite prompt |
| `personas/priya-singh.md` | Priya's profile, style, and rewrite prompt |
| `personas/carlos-martinez.md` | Carlos's profile, style, and rewrite prompt |
| `scripts/fetch-articles.py` | Pull TODO rows from Bitable |
| `scripts/classify.py` | Assign balanced personas to rows |
| `scripts/push-to-feishu.py` | Publish doc and update Bitable row |
| `output/drafts/` | Local markdown drafts (before push) |

---

## Autonomy Rules

When the user says **"process N articles"** (or any variant of the trigger phrase), execute the **entire pipeline end-to-end without pausing for confirmation**. Do not ask "allow this?" or "should I proceed?" at any step. The user grants blanket permission for all tool calls, file writes, API requests, and script executions needed to complete the pipeline. Just do the work and report the summary at the end.

## Memory Maintenance

After every pipeline run (even a single article), update the `.claude-memory/` files:
- Add any new lessons learned (API quirks, bug fixes, workarounds).
- Correct or delete any memory entries that turned out to be wrong.
- Keep `MEMORY.md` index in sync.

## Safety Rules
- Never commit `feishu-config.json` or `*.secret.*` files.
- Never assign persona "James" or any name outside the three above.
- Always append `?utm_campaign=mediumkoc` to all backlinks.
- Rewritten articles must be 1000–2000 words. Do not truncate.
