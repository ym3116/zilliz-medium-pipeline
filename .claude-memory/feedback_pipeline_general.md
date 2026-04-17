---
name: General pipeline execution tips
description: Practical tips for running the full article processing pipeline end-to-end
type: feedback
---
Lessons from running the pipeline:

**Draft reuse:** Check `output/drafts/{record_id}.md` before rewriting — a draft may already exist from a previous run. Verify word count (1000-2000) and backlink presence before reusing.

**Persona pre-assignment:** Many Bitable rows already have a `Target Account` (persona) assigned. If it's one of the three valid personas (Alex Chen, Priya Singh, Carlos Martinez), accept it instead of re-running classify.py. If it's "James" or another invalid persona, re-classify.

**Backlink insertion checklist:**
- Always append `?utm_campaign=mediumkoc` to every URL
- Link each keyword at most once (first occurrence in body text)
- Skip keywords inside code blocks and `#` headings
- Use longest-match-first priority (e.g. "Zilliz Cloud" before "Zilliz", "embedding model" before "embedding")
- Bold text (`**...**`) is NOT a heading — keywords in bold CAN be linked

**Feishu base_url:** The config has no `base_url` set, so doc URLs default to `bytedance.feishu.cn`. The Feishu Drive API returns `zilliverse.feishu.cn` URLs (e.g. for folder creation). Both appear to work, but the user's actual tenant is `zilliverse.feishu.cn`.

**Feishu folder management:** The "SEO Reposts" folder (token `OmH3fQT3QlEx1ldBuDUctQlrnId`) is the current output folder. Creating folders uses `POST /drive/explorer/v2/folder/{folderToken}` with `{"title": "name"}`. Root folder token can be fetched from `/drive/explorer/v2/root_folder/meta`.
