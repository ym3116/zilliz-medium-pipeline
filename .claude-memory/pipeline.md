---
name: Pipeline execution rules and tips
description: Rules for running the article pipeline — fetching, personas, backlinks, Feishu output
type: feedback
---

## Article fetching (Step 3a)

Use `requests` + `BeautifulSoup`, **not** the WebFetch tool — milvus.io URLs cause infinite redirect loops with WebFetch.

```python
headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
resp = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
soup = BeautifulSoup(resp.text, "html.parser")
for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
    tag.decompose()
text = soup.get_text(separator="\n", strip=True)
```

## Persona rules

- Valid personas: **Alex Chen, Priya Singh, Carlos Martinez** only. Never assign James or any other name.
- If a Bitable row already has a valid `Target Account`, accept it — skip re-classification.
- If it says "James" or anything else, re-classify.

## Backlink rules (Step 3e)

- Append `?utm_campaign=mediumkoc` to every URL
- Link each keyword **first occurrence only** in the body
- **Skip** keywords inside code blocks or `#` headings
- Bold text (`**...**`) is not a heading — keywords in bold **can** be linked
- Longest-match-first: "Zilliz Cloud" before "Zilliz", "embedding model" before "embedding"

## Output rules

- **No local drafts.** Pass rewritten markdown directly to `push_article()` — do not write to `output/drafts/` (directory deleted).
- Cover images go to `output/covers/<title>.png` (gitignored).

## Feishu output

- Output folder token: `OmH3fQT3QlEx1ldBuDUctQlrnId` (SEO Reposts folder, set in `feishu-config.json`)
- Doc URLs default to `bytedance.feishu.cn` — user's actual tenant is `zilliverse.feishu.cn`
