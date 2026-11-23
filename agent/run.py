"""Main runner CLI for Composio Toolkit Research pipeline.

Usage:
  python -m agent.run --pass 1 [--all] [--app "Name"]
  python -m agent.run --pass 2 [--all] [--app "Name"]
  python -m agent.run --pass 3 [--all]
"""

import os
import csv
import json
import argparse
from typing import List, Dict, Any, Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from agent.schema import AppResearchRecord
from agent.extract import extract_pass1, extract_pass2
from agent.verify import run_full_verification
from agent.review_queue import export_review_queue


def load_apps(apps_csv: str = "data/apps.csv") -> List[Dict[str, str]]:
    with open(apps_csv, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_existing_results(jsonl_path: str) -> Dict[int, AppResearchRecord]:
    results = {}
    path = Path(jsonl_path)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        rec = AppResearchRecord.model_validate(data)
                        results[rec.id] = rec
                    except Exception:
                        pass
    return results


def save_results(jsonl_path: str, records: List[AppResearchRecord]):
    unique = {r.id: r for r in records}
    sorted_records = sorted(unique.values(), key=lambda x: x.id)
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for rec in sorted_records:
            f.write(rec.model_dump_json() + "\n")


def export_csv(csv_path: str, records: List[AppResearchRecord]):
    if not records:
        return
    flat_rows = [rec.to_flat_dict() for rec in records]
    fieldnames = list(flat_rows[0].keys())
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flat_rows)


def run_pass1(apps: List[Dict[str, str]], concurrency: int = 5, resume: bool = True) -> List[AppResearchRecord]:
    output_path = "data/results_pass1.jsonl"
    existing = load_existing_results(output_path) if resume else {}
    records: List[AppResearchRecord] = list(existing.values())
    pending = [a for a in apps if int(a["id"]) not in existing]

    print(f"Running Pass 1 (Baseline) on {len(pending)} pending apps (concurrency={concurrency})...")

    def process_app(app_row: Dict[str, str]) -> Optional[AppResearchRecord]:
        try:
            return extract_pass1(
                app_id=int(app_row["id"]),
                name=app_row["name"],
                category=app_row["category"],
                hint=app_row.get("hint", ""),
            )
        except Exception as e:
            print(f"[Error] Pass 1 failed for {app_row['name']}: {e}")
            return None

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task("[cyan]Processing Pass 1...", total=len(pending))

        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            future_to_app = {executor.submit(process_app, app): app for app in pending}
            for future in as_completed(future_to_app):
                rec = future.result()
                if rec:
                    records.append(rec)
                    # Append immediately for resilience
                    with open(output_path, "a", encoding="utf-8") as f:
                        f.write(rec.model_dump_json() + "\n")
                progress.advance(task)

    records.sort(key=lambda x: x.id)
    save_results(output_path, records)
    print(f"Pass 1 complete. Saved {len(records)} records to {output_path}")
    return records


def run_pass2(apps: List[Dict[str, str]], concurrency: int = 5, resume: bool = True) -> List[AppResearchRecord]:
    output_path = "data/results_pass2.jsonl"
    existing = load_existing_results(output_path) if resume else {}
    records: List[AppResearchRecord] = list(existing.values())
    pending = [a for a in apps if int(a["id"]) not in existing]

    print(f"Running Pass 2 (Multi-Angle Pipeline) on {len(pending)} pending apps (concurrency={concurrency})...")

    def process_app(app_row: Dict[str, str]) -> Optional[AppResearchRecord]:
        try:
            return extract_pass2(
                app_id=int(app_row["id"]),
                name=app_row["name"],
                category=app_row["category"],
                hint=app_row.get("hint", ""),
            )
        except Exception as e:
            print(f"[Error] Pass 2 failed for {app_row['name']}: {e}")
            return None

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task("[green]Processing Pass 2...", total=len(pending))

        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            future_to_app = {executor.submit(process_app, app): app for app in pending}
            for future in as_completed(future_to_app):
                rec = future.result()
                if rec:
                    records.append(rec)
                    with open(output_path, "a", encoding="utf-8") as f:
                        f.write(rec.model_dump_json() + "\n")
                progress.advance(task)

    records.sort(key=lambda x: x.id)
    save_results(output_path, records)
    print(f"Pass 2 complete. Saved {len(records)} records to {output_path}")
    return records


def run_pass3() -> List[AppResearchRecord]:
    input_path = "data/results_pass2.jsonl"
    output_path = "data/results_pass3.jsonl"

    pass2_records = list(load_existing_results(input_path).values())
    if not pass2_records:
        raise ValueError("Pass 2 results not found. Please run Pass 2 first.")

    print(f"Running Pass 3 (Verification & Rule Checks) on {len(pass2_records)} records...")
    verified_records = []
    all_review_items = []

    for rec in pass2_records:
        v_rec, flags = run_full_verification(rec)
        verified_records.append(v_rec)
        all_review_items.extend(flags)

    verified_records.sort(key=lambda x: x.id)
    save_results(output_path, verified_records)

    # Export review queue
    review_summary = export_review_queue(all_review_items)
    print(f"Pass 3 complete. Saved {len(verified_records)} records to {output_path}.")
    print(f"Review queue exported to {review_summary['csv_path']} ({review_summary['total_flagged']} items).")
    print(f"Composio integration status: {review_summary['composio_status']}")
    return verified_records


def main():
    parser = argparse.ArgumentParser(description="Composio Toolkit Research Runner")
    parser.add_argument("--pass", dest="pass_num", choices=["1", "2", "3", "all"], default="all")
    parser.add_argument("--app", dest="app_name", help="Run research for a specific app by name")
    parser.add_argument("--concurrency", type=int, default=5, help="Concurrent workers")
    parser.add_argument("--no-resume", action="store_true", help="Do not resume from existing results")

    args = parser.parse_args()
    apps = load_apps()

    if args.app_name:
        apps = [a for a in apps if a["name"].lower() == args.app_name.lower()]
        if not apps:
            print(f"App '{args.app_name}' not found in data/apps.csv")
            return
        print(f"Filtering to single app: {apps[0]['name']}")

    resume = not args.no_resume

    if args.pass_num in ["1", "all"]:
        run_pass1(apps, concurrency=args.concurrency, resume=resume)

    if args.pass_num in ["2", "all"]:
        run_pass2(apps, concurrency=args.concurrency, resume=resume)

    if args.pass_num in ["3", "all"]:
        run_pass3()


if __name__ == "__main__":
    main()
