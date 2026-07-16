from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[3]
KNOWLEDGE_DIR = ROOT / "data" / "knowledge" / "huangshan"


def main() -> int:
    api_base_url = os.getenv("DIFY_KNOWLEDGE_API_BASE_URL", "https://api.dify.ai/v1").rstrip("/")
    api_key = os.getenv("DIFY_KNOWLEDGE_API_KEY")
    dataset_id = os.getenv("DIFY_DATASET_ID")

    if not api_key or not dataset_id:
        print("Missing DIFY_KNOWLEDGE_API_KEY or DIFY_DATASET_ID")
        return 1

    markdown_files = sorted(KNOWLEDGE_DIR.glob("*.md"))
    if not markdown_files:
        print(f"No markdown files found in {KNOWLEDGE_DIR}")
        return 1

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    endpoint = f"{api_base_url}/datasets/{dataset_id}/document/create-by-text"

    with httpx.Client(timeout=60) as client:
        for path in markdown_files:
            text = path.read_text(encoding="utf-8")
            payload = {
                "name": path.stem,
                "text": text,
                "indexing_technique": os.getenv("DIFY_INDEXING_TECHNIQUE", "high_quality"),
                "process_rule": {"mode": "automatic"},
            }
            response = client.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()
            print(f"uploaded: {path.name}")

    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
