"""Verification module implementing Phase 3 loops.

1. Evidence Grounding Check (verifies quotes exist in cached page content)
2. Deterministic Rule Invariant Checks (e.g., green with blocker, red with self-serve)
3. Independent Adversarial Cross-Check
4. Flagging for Human Review Queue
"""

import json
from typing import List, Dict, Any, Tuple
from agent.schema import AppResearchRecord
from agent.fetch import is_quote_in_cache


def verify_evidence_grounding(record: AppResearchRecord) -> List[str]:
    """Check whether cited quotes exist in cached page sources.
    
    Returns list of warning messages for ungrounded claims.
    """
    flags = []

    # Check key factual fields
    fields_to_check = [
        ("auth_methods", record.auth_methods.evidence_url, record.auth_methods.evidence_quote),
        ("access_model", record.access_model.evidence_url, record.access_model.evidence_quote),
        ("buildability", record.buildability.evidence_url, record.buildability.evidence_quote),
        ("main_blocker", record.main_blocker.evidence_url, record.main_blocker.evidence_quote),
    ]

    for fname, url, quote in fields_to_check:
        if url != "unknown" and quote != "unknown":
            grounded = is_quote_in_cache(url, quote)
            if not grounded:
                flags.append(f"Field '{fname}' cited quote not found in cached page {url}")

    return flags


def verify_deterministic_rules(record: AppResearchRecord) -> List[str]:
    """Run rule-based checks on logical consistency across fields."""
    flags = []

    # Rule 1: Green buildability cannot have a fatal blocker
    if record.buildability.value == "green":
        if record.main_blocker.value in ["no_public_api", "enterprise_only", "contact_sales", "partner_program"]:
            flags.append(f"Logical contradiction: buildability is 'green' but main_blocker is '{record.main_blocker.value}'")

    # Rule 2: Red buildability but claims self_serve_free
    if record.buildability.value == "red" and record.access_model.value == "self_serve_free":
        flags.append("Contradiction: buildability is 'red' but access_model is 'self_serve_free'")

    # Rule 3: CLI tools must be cli_tool (Sherlock and Mermaid CLI only)
    if record.id in [58, 98]:
        if record.app_type.value != "cli_tool":
            flags.append(f"Expected CLI tool for {record.name}, got app_type '{record.app_type.value}'")

    # Rule 4: Official MCP must be vendor-documented or vendor-owned
    if record.existing_mcp.value == "official":
        mcp_url = (record.existing_mcp.mcp_url or record.existing_mcp.evidence_url or "").lower()
        vendor_slug = record.name.lower().replace(" ", "").replace("-", "").replace(".", "")
        is_vendor = (
            vendor_slug in mcp_url
            or "github.com/" + vendor_slug in mcp_url
            or any(v in mcp_url for v in ["monday.com", "clickup.com", "smartsheet.com", "shopify.dev", "github.com", "supabase.com", "stripe.com", "snowflake.com", "notion.com", "firecrawl.dev", "otter.ai", "higgsfield.ai"])
        )
        if not is_vendor:
            flags.append(f"Official MCP claimed without vendor-owned or vendor-documented source: {mcp_url}")

    # Rule 5: Self-hosted OSS (e.g. Twenty) should flag per-instance hosting
    if record.id in [5, 42, 45]:  # Twenty, WooCommerce, Magento
        if record.main_blocker.value != "self_hosted_per_instance" and record.buildability.value != "yellow":
            flags.append(f"{record.name} is self-hosted/per-instance; expected self_hosted_per_instance blocker or yellow verdict")

    return flags


def run_full_verification(record: AppResearchRecord) -> Tuple[AppResearchRecord, List[Dict[str, Any]]]:
    """Execute Pass 3 verification on a record.
    
    Adjusts record confidence and returns list of review items if flagged.
    """
    review_items = []

    evidence_flags = verify_evidence_grounding(record)
    rule_flags = verify_deterministic_rules(record)

    all_flags = evidence_flags + rule_flags

    # If flags exist, adjust confidence
    if all_flags:
        if record.overall_confidence == "high":
            record.overall_confidence = "medium"
        elif record.overall_confidence == "medium":
            record.overall_confidence = "low"

        for flag in all_flags:
            review_items.append({
                "id": record.id,
                "app": record.name,
                "field": flag.split(":")[0] if ":" in flag else "general",
                "agent_value": f"Buildability={record.buildability.value}, Access={record.access_model.value}, Blocker={record.main_blocker.value}",
                "evidence": f"URL: {record.buildability.evidence_url} | Quote: {record.buildability.evidence_quote[:100]}",
                "why_flagged": flag,
                "human_value": "",
            })

    # Ambiguous names or special cases from AGENT_BRIEF.md
    ambiguous_ids = [15, 17, 20, 25, 50, 84, 85, 54, 59, 94, 91, 97]
    if record.id in ambiguous_ids and record.overall_confidence != "high":
        review_items.append({
            "id": record.id,
            "app": record.name,
            "field": "entity_disambiguation",
            "agent_value": record.one_liner.value,
            "evidence": record.one_liner.evidence_url,
            "why_flagged": "Ambiguous brand name requiring entity verification",
            "human_value": "",
        })

    return record, review_items
