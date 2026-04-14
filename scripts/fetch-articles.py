"""
fetch-articles.py

Reads all rows from the configured Feishu Bitable table and returns only
rows where Status = TODO. Each row includes: record_id, Source Link,
Target Account, and Repurposed Title.

Usage:
    python fetch-articles.py
"""

import json
import os
import sys

import requests

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../config/feishu-config.json")


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def get_tenant_access_token(config):
    """Get a short-lived tenant access token from the Feishu open platform."""
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


def extract_url(field_value):
    """Extract a plain URL string from a Feishu URL/link field (array of objects or plain string)."""
    if isinstance(field_value, list) and field_value:
        return field_value[0].get("link", "")
    if isinstance(field_value, str):
        return field_value
    return ""


def extract_text(field_value):
    """Extract plain text from a Feishu text or rich-text field."""
    if isinstance(field_value, list):
        parts = []
        for item in field_value:
            if isinstance(item, dict):
                parts.append(item.get("text", ""))
            elif isinstance(item, str):
                parts.append(item)
        return "".join(parts).strip()
    if isinstance(field_value, str):
        return field_value.strip()
    return ""


def fetch_todo_rows():
    """
    Return all rows where Status = TODO from the Bitable table.

    Returns:
        list of dict, each with keys:
            record_id       (str)
            source_link     (str)   — article URL
            target_account  (str)   — assigned persona (may be empty)
            repurposed_title (str)  — target title for the rewrite
    """
    config = load_config()
    token = get_tenant_access_token(config)
    headers = {"Authorization": f"Bearer {token}"}

    app_token = config["bitable_app_token"]
    table_id = config["bitable_table_id"]
    base_url = (
        f"https://open.feishu.cn/open-apis/bitable/v1"
        f"/apps/{app_token}/tables/{table_id}/records"
    )

    rows = []
    page_token = None

    while True:
        params = {
            "filter": 'CurrentValue.[Status]="TODO"',
            "page_size": 100,
        }
        if page_token:
            params["page_token"] = page_token

        resp = requests.get(base_url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != 0:
            raise RuntimeError(f"Bitable API error: {data}")

        for record in data["data"]["items"]:
            fields = record["fields"]
            rows.append(
                {
                    "record_id": record["record_id"],
                    "source_link": extract_url(fields.get("Source Link", "")),
                    "target_account": extract_text(fields.get("Target Account", "")),
                    "repurposed_title": extract_text(
                        fields.get("Repurposed Title", "")
                    ),
                }
            )

        if not data["data"].get("has_more"):
            break
        page_token = data["data"]["page_token"]

    return rows


if __name__ == "__main__":
    rows = fetch_todo_rows()
    print(f"Found {len(rows)} TODO rows:")
    for row in rows:
        print(
            f"  [{row['record_id']}] "
            f"{row['source_link']!r} | "
            f"persona={row['target_account']!r} | "
            f"title={row['repurposed_title']!r}"
        )
