# Composio Toolkit Research: 100-App Feasibility Matrix

Autonomous research pipeline assessing 100 target applications and SaaS APIs for Composio agent toolkits, Model Context Protocol (MCP) servers, and agent-callable tools.

**Live Interactive Case Study:** [https://sushanth-xy.github.io/composio-toolkit-research/](https://sushanth-xy.github.io/composio-toolkit-research/)  
**GitHub Repository:** [https://github.com/Sushanth-xy/composio-toolkit-research](https://github.com/Sushanth-xy/composio-toolkit-research)

---

## What It Does

Before investing engineering hours into building Composio toolkits across hundreds of third-party platforms, teams must understand:
1. **Authentication:** OAuth2 (authorization code, PKCE, client credentials), API keys, Basic auth, or session tokens.
2. **Access & Gating:** Can individual developers self-serve credentials for free or on trial, or does it require a paid tier, admin approval, partner agreements, or contact-sales gating?
3. **API Breadth:** REST, GraphQL, OpenAPI specification availability, webhooks, rate limits.
4. **MCP Readiness:** Existing official or community Model Context Protocol servers.
5. **Toolkit Feasibility:** Green (ready today), Yellow (buildable with effort/gating), Red (blocked/no public API).
6. **Verifiable Grounding:** Every single factual claim is anchored by verbatim documentation quotes and source URLs.

---

## Quickstart & Installation

```bash
# 1. Clone repository
git clone https://github.com/Sushanth-xy/composio-toolkit-research.git
cd composio-toolkit-research

# 2. Create and activate virtual environment (Python 3.11+)
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env with your GEMINI_API_KEY, COMPOSIO_API_KEY, and TAVILY_API_KEY
```

---

## Running the Agent

### Research a Single App
Run extraction and grounded evaluation for any application by name:
```bash
python -m agent.run --pass 2 --app "Attio"
```

### Run Full Multi-Pass Pipeline Across All 100 Apps
```bash
# Pass 1: Baseline extraction (single LLM call + top search page)
python -m agent.run --pass 1

# Pass 2: Multi-angle grounded pipeline (multi-query search, page caching, MCP check)
python -m agent.run --pass 2

# Pass 3: Verification loops & rule checks (quote validation, review queue export)
python -m agent.run --pass 3
```

### Run Accuracy Evaluation
Compare pipeline passes against verified Gold benchmark across 30 stratified sample apps:
```bash
python -m analysis.accuracy
```

### Generate Pattern Analytics & Interactive Case Study
```bash
python -m analysis.patterns
python site/build_site.py
```

---

## Where Outputs Land

- `data/apps.csv`: Source seed catalog of 100 target applications (Appendix A).
- `data/results_pass1.jsonl`: Baseline ungrounded extraction results.
- `data/results_pass2.jsonl`: Multi-query grounded pipeline results with verbatim evidence.
- `data/results_pass3.jsonl`: Verified results post-rule checks and quote validation.
- `data/results_final.jsonl` & `.csv`: Final audited dataset with human review triage applied.
- `data/quote_audit.csv` & `.json`: Verbatim quote audit tracking char offsets and grounded agent inferences.
- `data/gold_holdout.csv`: 18-app stratified hold-out benchmark template for human documentation audit.
- `data/review.csv`: Review queue containing flagged low-confidence or ambiguous items.
- `site/index.html`: Fully self-contained responsive case study dashboard deployed to GitHub Pages.

---

## Pipeline Architecture & Verification Loops

```
Discover (5 Targeted Queries) ──► Fetch & Cache (SHA256) ──► MCP & Composio Catalog
                                                                     │
Human Review Queue ◄── Rule Invariant Checks ◄── Grounded Extraction (Gemini)
        │
Final Verified Matrix & Interactive Dashboard (GitHub Pages)
```

1. **Evidence Grounding Loop:** Every cited quote is verified against the cached HTML/Markdown text. Missing quotes are downgraded or flagged.
2. **Rule Invariant Checks:** Detects logical contradictions (e.g., Green buildability paired with partner program blockers; CLI tools classified as hosted SaaS).
3. **Human Review Queue:** Ambiguous entities and flagged items are routed to `data/review.csv` and pushed to Composio integration.

---

## Known Limits & Nuances

- **Multi-Tenant vs Single-Dev Distinction:** A single developer can often generate an API key self-serve, but building a managed Composio OAuth integration may require formal app review (e.g., Google Ads developer token, Meta Ads review, Amazon SP-API registration).
- **Per-Instance Hosting:** Open-source platforms like Twenty, WooCommerce, or Magento require per-instance base URL routing.
- **Composio SDK Integration:** Demonstrated via the review queue export. The SDK v3 transition requires connected OAuth account verification links; automated fallback routes to `data/review.csv`.
