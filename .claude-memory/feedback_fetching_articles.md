---
name: Article fetching methods
description: What works and what fails when fetching article content from source URLs (e.g. milvus.io blog posts)
type: feedback
---
Use Python `requests` + `BeautifulSoup` to fetch articles, NOT the WebFetch tool.

**Why:** milvus.io blog URLs (e.g. `.md` suffix) cause infinite redirect loops with WebFetch (>10 redirects). Python requests with a browser-like User-Agent header handles them fine and returns 200.

**How to apply:** When Step 3a says "fetch the full article text from source_link", always use a Python script approach:
```python
import requests
from bs4 import BeautifulSoup
headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ..."}
resp = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
soup = BeautifulSoup(resp.text, "html.parser")
for tag in soup(["script","style","nav","footer","header","aside"]):
    tag.decompose()
text = soup.get_text(separator="\n", strip=True)
```

Note: the `extract_url()` bug in `fetch-articles.py` (Source Link field being a dict) was fixed on 2026-04-17 by adding a `isinstance(field_value, dict)` check.
