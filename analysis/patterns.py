"""Pattern analysis module for Composio Toolkit Research.

Computes distributions, cross-tabulations, segments, priority scores,
blocker rankings (excluding 'none'), auth-by-category metrics, and
recommended build orders from research results.
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from agent.schema import AppResearchRecord


def load_records(jsonl_path: str = "data/results_final.jsonl") -> List[AppResearchRecord]:
    path = Path(jsonl_path)
    if not path.exists():
        path = Path("data/results_pass3.jsonl")
    if not path.exists():
        path = Path("data/results_pass2.jsonl")
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(AppResearchRecord.model_validate_json(line))
    return records


def analyze_patterns(records: List[AppResearchRecord]) -> Dict[str, Any]:
    total_apps = len(records)
    if total_apps == 0:
        return {}

    # 1. Auth Distribution overall & by category
    auth_overall = {}
    auth_by_category = {}
    for r in records:
        cat = r.category.value
        if cat not in auth_by_category:
            auth_by_category[cat] = {}
        for m in r.auth_methods.value:
            auth_overall[m] = auth_overall.get(m, 0) + 1
            auth_by_category[cat][m] = auth_by_category[cat].get(m, 0) + 1

    # 2. Access Model Distribution & Category x Access Model Matrix
    access_overall = {}
    cat_x_access = {}
    for r in records:
        cat = r.category.value
        acc = r.access_model.value
        access_overall[acc] = access_overall.get(acc, 0) + 1
        if cat not in cat_x_access:
            cat_x_access[cat] = {}
        cat_x_access[cat][acc] = cat_x_access[cat].get(acc, 0) + 1

    # 3. Blockers Analysis: Exclude 'none' when ranking blockers
    blockers_all = {}
    real_blockers = {}
    for r in records:
        b = r.main_blocker.value
        blockers_all[b] = blockers_all.get(b, 0) + 1
        if b != "none":
            real_blockers[b] = real_blockers.get(b, 0) + 1

    ranked_real_blockers = sorted(real_blockers.items(), key=lambda x: x[1], reverse=True)
    none_blocker_count = blockers_all.get("none", 0)

    # 4. Buildability overall & by category
    buildability_overall = {"green": 0, "yellow": 0, "red": 0}
    buildability_by_category = {}
    for r in records:
        v = r.buildability.value
        cat = r.category.value
        buildability_overall[v] = buildability_overall.get(v, 0) + 1
        if cat not in buildability_by_category:
            buildability_by_category[cat] = {"green": 0, "yellow": 0, "red": 0}
        buildability_by_category[cat][v] = buildability_by_category[cat].get(v, 0) + 1

    # 5. Existing MCP & Already in Composio
    mcp_coverage = {"official": 0, "community": 0, "none": 0}
    composio_coverage = {"yes": 0, "no": 0, "unknown": 0}
    for r in records:
        mcp_coverage[r.existing_mcp.value] = mcp_coverage.get(r.existing_mcp.value, 0) + 1
        composio_coverage[r.already_in_composio.value] = composio_coverage.get(r.already_in_composio.value, 0) + 1

    # 6. OpenAPI Spec vs Buildability
    openapi_counts = {"yes": 0, "no": 0, "unknown": 0}
    openapi_vs_green = {"yes": 0, "no": 0, "unknown": 0}
    for r in records:
        spec = r.openapi_spec.value
        openapi_counts[spec] = openapi_counts.get(spec, 0) + 1
        if r.buildability.value == "green":
            openapi_vs_green[spec] = openapi_vs_green.get(spec, 0) + 1

    # 7. Strategic Segments: Easy Wins vs Needs Outreach vs Configuration Required vs Not a Fit
    easy_wins = []
    needs_outreach = []
    not_a_fit = []
    requires_configuration = []

    for r in records:
        is_green = r.buildability.value == "green"
        is_self_serve = r.access_model.value in ["self_serve_free", "self_serve_trial"]

        # Easy wins MUST strictly be green AND self_serve_free or self_serve_trial
        if is_green and is_self_serve:
            easy_wins.append({
                "id": r.id,
                "name": r.name,
                "category": r.category.value,
                "access": r.access_model.value,
                "openapi": r.openapi_spec.value,
                "auth": r.auth_methods.value,
                "mcp": r.existing_mcp.value,
            })
        elif r.main_blocker.value in ["partner_program", "contact_sales", "app_review"]:
            needs_outreach.append({
                "id": r.id,
                "name": r.name,
                "category": r.category.value,
                "blocker": r.main_blocker.value,
                "reason": r.reasoning,
                "buildability": r.buildability.value,
            })
        elif r.app_type.value == "cli_tool" or r.main_blocker.value == "no_public_api":
            not_a_fit.append({
                "id": r.id,
                "name": r.name,
                "category": r.category.value,
                "blocker": r.main_blocker.value,
            })
        else:
            requires_configuration.append({
                "id": r.id,
                "name": r.name,
                "category": r.category.value,
                "access": r.access_model.value,
                "blocker": r.main_blocker.value,
                "buildability": r.buildability.value,
                "reason": r.reasoning,
            })

    # Sort segments by ID
    easy_wins.sort(key=lambda x: x["id"])
    needs_outreach.sort(key=lambda x: x["id"])
    not_a_fit.sort(key=lambda x: x["id"])
    requires_configuration.sort(key=lambda x: x["id"])

    # 8. Priority Scoring & Top-15 Build Order
    scored_apps = []
    for r in records:
        ease = 10 if r.buildability.value == "green" else (5 if r.buildability.value == "yellow" else 1)
        breadth_mult = 1.3 if r.api_breadth.value == "broad" else (1.0 if r.api_breadth.value == "medium" else 0.7)
        bonus = (3 if r.openapi_spec.value == "yes" else 0) + (2 if r.access_model.value == "self_serve_free" else 0)
        penalty = 3 if r.main_blocker.value in ["app_review", "partner_program", "contact_sales"] else 0
        cat_weight = 1.2 if r.category.value in ["CRM and Sales", "Support and Helpdesk", "Developer/Infra/Data"] else 1.0

        score = round((ease * breadth_mult + bonus - penalty) * cat_weight, 1)

        scored_apps.append({
            "id": r.id,
            "name": r.name,
            "category": r.category.value,
            "score": score,
            "buildability": r.buildability.value,
            "access_model": r.access_model.value,
            "already_in_composio": r.already_in_composio.value,
            "one_liner": r.one_liner.value,
            "reasoning": r.reasoning,
        })

    new_opportunities = [a for a in scored_apps if a["already_in_composio"] != "yes"]
    new_opportunities.sort(key=lambda x: x["score"], reverse=True)
    top_15_build_order = new_opportunities[:15]

    # Category Auth Insights
    crm_oauth = auth_by_category.get("CRM and Sales", {}).get("oauth2", 0)
    crm_total = sum(1 for r in records if r.category.value == "CRM and Sales")
    dev_key = auth_by_category.get("Developer/Infra/Data", {}).get("api_key", 0)
    dev_total = sum(1 for r in records if r.category.value == "Developer/Infra/Data")

    # Top real blockers summary string
    top_real_blockers_str = ", ".join(f"{b} ({c})" for b, c in ranked_real_blockers[:3])

    # Rewrite headline patterns
    headlines = [
        f"Real Blocker Ranking: Gating analysis across restricted platforms reveals {top_real_blockers_str} as the primary architectural bottlenecks. Managed OAuth scopes and partner review queues represent the highest integration friction.",
        f"Portfolio Velocity Split: {len(easy_wins)} Easy Wins (self-serve free/trial APIs) vs {len(needs_outreach)} Outreach Targets (gated behind partner reviews or sales agreements) vs {len(requires_configuration)} Configuration-Dependent (paid/self-hosted/admin) vs {len(not_a_fit)} CLI/No-API Tools (Total: {total_apps}).",
        f"Authentication Architecture by Category: CRM & Messaging mandate OAuth2 ({crm_oauth}/{crm_total} CRM apps), whereas Developer Infra & Scraping rely primarily on API Keys ({dev_key}/{dev_total} Dev apps) for headless machine execution.",
        f"Catalog Feasibility: {buildability_overall['green']} apps immediately buildable today, {buildability_overall['yellow']} requiring partner provisioning or containerized execution, and {buildability_overall['red']} lacking public developer APIs.",
    ]

    summary = {
        "total_apps": total_apps,
        "headlines": headlines,
        "auth_overall": auth_overall,
        "auth_by_category": auth_by_category,
        "access_overall": access_overall,
        "cat_x_access": cat_x_access,
        "ranked_real_blockers": ranked_real_blockers,
        "ranked_blockers": ranked_real_blockers,  # for backwards compatibility
        "none_blocker_count": none_blocker_count,
        "buildability_overall": buildability_overall,
        "buildability_by_category": buildability_by_category,
        "mcp_coverage": mcp_coverage,
        "composio_coverage": composio_coverage,
        "openapi_counts": openapi_counts,
        "openapi_vs_green": openapi_vs_green,
        "easy_wins_count": len(easy_wins),
        "needs_outreach_count": len(needs_outreach),
        "not_a_fit_count": len(not_a_fit),
        "requires_configuration_count": len(requires_configuration),
        "easy_wins": easy_wins,
        "needs_outreach": needs_outreach,
        "not_a_fit": not_a_fit,
        "requires_configuration": requires_configuration,
        "top_15_build_order": top_15_build_order,
    }

    output_path = Path("data/patterns.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary


if __name__ == "__main__":
    records = load_records()
    print(f"Loaded {len(records)} records.")
    results = analyze_patterns(records)
    print("Pattern analysis complete.")
    for h in results.get("headlines", []):
        print("-", h)
