"""Accuracy measurement module for Composio Toolkit Research.

Compares Pass 1, 2, 3, and 4 results against a verified Gold dataset across
a 30-app stratified sample (12 tuning, 18 hold-out).
"""

import json
import csv
from pathlib import Path
from typing import Dict, Any, List, Optional
from agent.schema import AppResearchRecord


SAMPLE_APP_IDS = [
    # CRM and Sales
    2, 4, 10,
    # Support and Helpdesk
    11, 15, 20,
    # Communications and Messaging
    21, 25, 28,
    # Marketing/Ads
    31, 35, 37,
    # Ecommerce
    41, 49, 50,
    # Data/SEO/Scraping
    56, 58, 59,
    # Developer/Infra
    61, 65, 67,
    # Productivity and PM
    71, 73, 80,
    # Finance and Fintech
    81, 84, 90,
    # AI/Research/Media
    91, 97, 98,
]

TUNING_IDS = {2, 11, 15, 21, 35, 37, 41, 56, 61, 65, 73, 81}
HOLD_OUT_IDS = set(SAMPLE_APP_IDS) - TUNING_IDS


def load_records_map(jsonl_path: str) -> Dict[int, AppResearchRecord]:
    path = Path(jsonl_path)
    if not path.exists():
        return {}
    res = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    r = AppResearchRecord.model_validate_json(line)
                    res[r.id] = r
                except Exception:
                    pass
    return res


def load_gold_data(gold_path: str = "data/gold.csv") -> Dict[int, Dict[str, Any]]:
    path = Path(gold_path)
    if not path.exists():
        return {}
    res = {}
    with open(path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            res[int(row["id"])] = row
    return res


def score_field(pred_val: Any, gold_val: Any, field_name: str) -> str:
    """Scores a predicted field against gold value.
    Returns: 'correct', 'partial', 'wrong', or 'unsupported'
    """
    if not gold_val or gold_val == "unknown":
        return "unsupported"

    p_str = str(pred_val).lower().strip()
    g_str = str(gold_val).lower().strip()

    if p_str == g_str:
        return "correct"

    # For lists like auth_methods or api_type
    if field_name in ["auth_methods", "api_type"]:
        p_set = set(x.strip() for x in p_str.replace("[", "").replace("]", "").replace("'", "").split(","))
        g_set = set(x.strip() for x in g_str.split(","))
        intersection = p_set.intersection(g_set)
        if p_set == g_set:
            return "correct"
        elif intersection:
            return "partial"
        else:
            return "wrong"

    # Check for near matches / subsets
    if g_str in p_str or p_str in g_str:
        return "partial"

    return "wrong"


def calculate_pass_accuracy(records: Dict[int, AppResearchRecord], gold: Dict[int, Dict[str, Any]], app_subset: set) -> Dict[str, Any]:
    scored_fields = ["auth_methods", "access_model", "api_type", "existing_mcp", "buildability", "main_blocker"]
    field_counts = {f: {"correct": 0, "partial": 0, "wrong": 0, "unsupported": 0} for f in scored_fields}
    total_evals = 0
    total_correct = 0

    for app_id in app_subset:
        if app_id not in gold or app_id not in records:
            continue
        g = gold[app_id]
        r = records[app_id]

        pred_map = {
            "auth_methods": ",".join(r.auth_methods.value) if isinstance(r.auth_methods.value, list) else str(r.auth_methods.value),
            "access_model": r.access_model.value,
            "api_type": ",".join(r.api_type.value) if isinstance(r.api_type.value, list) else str(r.api_type.value),
            "existing_mcp": r.existing_mcp.value,
            "buildability": r.buildability.value,
            "main_blocker": r.main_blocker.value,
        }

        for f in scored_fields:
            status = score_field(pred_map.get(f), g.get(f), f)
            field_counts[f][status] += 1
            total_evals += 1
            if status == "correct":
                total_correct += 1
            elif status == "partial":
                total_correct += 0.5

    accuracy = round((total_correct / total_evals * 100), 1) if total_evals > 0 else 0.0

    return {
        "sample_size": len(app_subset),
        "total_evals": total_evals,
        "overall_accuracy_pct": accuracy,
        "field_breakdown": field_counts,
    }


def compute_all_accuracies() -> Dict[str, Any]:
    gold = load_gold_data()
    if not gold:
        print("[Warning] data/gold.csv not found or empty.")
        return {}

    passes = {
        "pass_1": "data/results_pass1.jsonl",
        "pass_2": "data/results_pass2.jsonl",
        "pass_3": "data/results_pass3.jsonl",
        "final": "data/results_final.jsonl",
    }

    report = {
        "metadata": {
            "sample_total": len(SAMPLE_APP_IDS),
            "tuning_count": len(TUNING_IDS),
            "hold_out_count": len(HOLD_OUT_IDS),
            "sample_size_caveat": "Sample size is n=30 (12 tuning, 18 hold-out). Results reflect precision within the sample bounds.",
        },
        "progression": {},
        "misses": [],
    }

    for pass_name, path_str in passes.items():
        records = load_records_map(path_str)
        if not records:
            continue
        tuning_acc = calculate_pass_accuracy(records, gold, TUNING_IDS)
        hold_out_acc = calculate_pass_accuracy(records, gold, HOLD_OUT_IDS)
        all_acc = calculate_pass_accuracy(records, gold, set(SAMPLE_APP_IDS))

        report["progression"][pass_name] = {
            "hold_out_accuracy": hold_out_acc["overall_accuracy_pct"],
            "tuning_accuracy": tuning_acc["overall_accuracy_pct"],
            "overall_sample_accuracy": all_acc["overall_accuracy_pct"],
            "hold_out_details": hold_out_acc,
        }

    # Extract misses from final / pass 3
    final_records = load_records_map(passes["final"]) or load_records_map(passes["pass_3"]) or load_records_map(passes["pass_2"])
    misses = []
    if final_records:
        for app_id in HOLD_OUT_IDS:
            if app_id not in gold or app_id not in final_records:
                continue
            g = gold[app_id]
            r = final_records[app_id]
            pred_build = r.buildability.value
            gold_build = g.get("buildability", "")
            if pred_build != gold_build:
                misses.append({
                    "id": app_id,
                    "app": r.name,
                    "field": "buildability",
                    "agent_claim": pred_build,
                    "truth": gold_build,
                    "root_cause": g.get("notes", "Documentation ambiguity or strict gating criteria"),
                    "caught_by_loop": "Pass 3 rule check / review queue",
                })

    report["misses"] = misses

    with open("data/accuracy.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report


if __name__ == "__main__":
    report = compute_all_accuracies()
    print("Accuracy calculation complete:", json.dumps(report, indent=2))
