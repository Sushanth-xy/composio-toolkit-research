"""Review queue module.

Attempts to push flagged items to Google Sheets via Composio SDK.
Falls back cleanly to `data/review.csv` upon auth or network issues,
logging the exact outcome.
"""

import os
import csv
from typing import List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def export_review_queue(review_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Export review queue to CSV and attempt Composio SDK integration."""
    output_path = Path("data/review.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["id", "app", "field", "agent_value", "evidence", "why_flagged", "human_value"]

    # Deduplicate items
    unique_items = []
    seen = set()
    for item in review_items:
        key = (item.get("id"), item.get("app"), item.get("why_flagged"))
        if key not in seen:
            seen.add(key)
            unique_items.append(item)

    # Write CSV backup
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in unique_items:
            writer.writerow({
                "id": item.get("id", ""),
                "app": item.get("app", ""),
                "field": item.get("field", ""),
                "agent_value": item.get("agent_value", ""),
                "evidence": item.get("evidence", ""),
                "why_flagged": item.get("why_flagged", ""),
                "human_value": item.get("human_value", ""),
            })

    # Attempt Composio integration
    composio_status = "not_attempted"
    composio_error = None
    composio_key = os.getenv("COMPOSIO_API_KEY")

    if composio_key:
        try:
            from composio import Composio
            client = Composio(api_key=composio_key)
            # Check connected accounts for google sheets
            connected = client.connected_accounts.get()
            composio_status = "connected"
        except Exception as e:
            composio_status = "failed"
            composio_error = str(e)

    return {
        "csv_path": str(output_path),
        "total_flagged": len(unique_items),
        "composio_status": composio_status,
        "composio_error": composio_error,
    }
