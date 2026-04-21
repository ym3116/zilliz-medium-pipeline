"""
classify.py

Takes a list of TODO rows (from fetch-articles.py), fetches each article's
content, and assigns the best-fit persona — keeping the total count balanced
across Alex Chen, Priya Singh, and Carlos Martínez.

Current persona counts are read from the full Bitable table (all rows, not
just TODO) so balance accounts for already-processed articles.

Usage:
    python classify.py             # reads rows via fetch-articles.py
    python classify.py rows.json   # reads rows from a JSON file
"""

import json
import os
import sys

import requests

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../config/feishu-config.json")

PERSONAS = ["Alex Chen", "Priya Singh", "Carlos Martínez"]

# Keyword sets that signal affinity for each persona.
# Longer keyword lists = finer signal; keep them distinct.
PERSONA_KEYWORDS = {
    "Alex Chen": [
        "benchmark", "performance", "throughput", "latency",
        "database internals", "storage engine", "indexing algorithm",
        "architecture", "c++", "golang", "memory allocation", "disk io",
        "HNSW", "IVF", "ANN", "approximate nearest neighbor",
        "compaction", "WAL", "LSM tree", "sharding", "replication",
        "profiling", "flamegraph", "memory footprint", "query plan",
        "PostgreSQL", "Apache Lucene", "RocksDB",
    ],
    "Priya Singh": [
        "RAG", "retrieval augmented generation", "LLM", "large language model",
        "langchain", "llamaindex", "openai", "chatbot", "chatgpt",
        "embedding", "sentence transformer", "semantic search",
        "pipeline", "tutorial", "step by step", "how to",
        "recommendation system", "pytorch", "tensorflow",
        "fine-tuning", "inference", "prompt engineering", "context window",
        "chunking", "vector store", "retrieval", "generation",
    ],
    "Carlos Martínez": [
        "enterprise", "business value", "ROI", "cost savings",
        "kafka", "flink", "kubernetes", "k8s", "ETL", "data pipeline",
        "devops", "infrastructure", "deployment", "production",
        "scalability", "security", "compliance", "SLA", "uptime",
        "data platform", "streaming", "real-time", "observability",
        "monitoring", "alerting", "war story", "lessons learned",
        "distributed system", "microservice", "data warehouse",
    ],
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


def extract_text(field_value):
    if isinstance(field_value, list):
        return "".join(
            item.get("text", "") if isinstance(item, dict) else item
            for item in field_value
        ).strip()
    if isinstance(field_value, str):
        return field_value.strip()
    return ""


def get_existing_persona_counts(config=None):
    """
    Query ALL rows in the Bitable table and count how many are already
    assigned to each persona (via Target Account field).

    Returns:
        dict: {"Alex Chen": int, "Priya Singh": int, "Carlos Martínez": int}
    """
    if config is None:
        config = load_config()

    token = get_tenant_access_token(config)
    headers = {"Authorization": f"Bearer {token}"}

    app_token = config["bitable_app_token"]
    table_id = config["bitable_table_id"]
    base_url = (
        f"https://open.feishu.cn/open-apis/bitable/v1"
        f"/apps/{app_token}/tables/{table_id}/records"
    )

    counts = {p: 0 for p in PERSONAS}
    page_token = None

    while True:
        params = {"page_size": 100}
        if page_token:
            params["page_token"] = page_token

        resp = requests.get(base_url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        for record in data["data"]["items"]:
            persona = extract_text(record["fields"].get("Target Account", ""))
            if persona in counts:
                counts[persona] += 1

        if not data["data"].get("has_more"):
            break
        page_token = data["data"]["page_token"]

    return counts


def fetch_article_text(url: str) -> str:
    """
    Fetch and return the plain text of an article at the given URL.
    Uses BeautifulSoup if available; falls back to raw HTML.
    """
    if not url:
        return ""
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()

        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()
            return soup.get_text(separator=" ", strip=True)
        except ImportError:
            return resp.text

    except Exception as e:
        print(f"  Warning: could not fetch {url}: {e}", file=sys.stderr)
        return ""


def score_article(text: str) -> dict:
    """Return a keyword-match score for each persona against the article text."""
    text_lower = text.lower()
    return {
        persona: sum(1 for kw in keywords if kw.lower() in text_lower)
        for persona, keywords in PERSONA_KEYWORDS.items()
    }


def classify_rows(todo_rows: list) -> list:
    """
    Assign a persona to each row in todo_rows, keeping running counts balanced.

    Strategy:
      - Fetch current persona counts from the full table.
      - For each article, score it against each persona's keyword set.
      - Select the persona that maximises score; break ties by picking
        the least-assigned persona so far.

    Args:
        todo_rows: list of row dicts (record_id, source_link, ...)

    Returns:
        Same list with 'assigned_persona' and 'scores' added to each row.
    """
    print("Fetching current persona assignment counts from full table...")
    counts = get_existing_persona_counts()
    print(f"  Existing counts: {counts}")

    results = []
    for row in todo_rows:
        url = row["source_link"]
        print(f"\n  Classifying: {url}")
        text = fetch_article_text(url)
        scores = score_article(text)

        # Rank: highest keyword score first; break ties by fewest existing assignments
        def rank_key(persona):
            return (-scores[persona], counts[persona])

        assigned = min(PERSONAS, key=rank_key)
        counts[assigned] += 1  # Update running count so next row sees it

        print(f"    Keyword scores: {scores}")
        print(f"    → Assigned: {assigned}")

        result = dict(row)
        result["assigned_persona"] = assigned
        result["scores"] = scores
        results.append(result)

    return results


if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            rows = json.load(f)
    else:
        # Pull live TODO rows from Bitable
        sys.path.insert(0, os.path.dirname(__file__))
        from fetch_articles import fetch_todo_rows  # type: ignore

        rows = fetch_todo_rows()

    classified = classify_rows(rows)
    print("\n--- Classification Results ---")
    for row in classified:
        print(f"  {row['record_id']} → {row['assigned_persona']}")


