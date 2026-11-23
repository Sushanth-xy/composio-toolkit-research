# Engineering & Execution Log: Composio Toolkit Research

This document tracks all design decisions, architectural choices, prompt iterations, pipeline executions, verification loops, failures, and human interventions throughout the Composio 100-app toolkit feasibility research project.

---

## 1. How It Works (Interview Reference Guide)

### Core Mission
Composio turns external applications and SaaS platforms into agentic tools that AI models can execute. To expand Composio's catalog systematically, we need an automated yet high-fidelity pipeline to assess 100 target SaaS/developer platforms across:
1. **Authentication protocols:** OAuth2 (flows, PKCE, device code), API keys, Basic auth, session tokens, etc.
2. **Access & Developer gating:** Self-serve free/trial vs paid tier requirements, admin approval, developer app review, or enterprise partnership gating.
3. **API surface & breadth:** REST, GraphQL, OpenAPI availability, webhook triggers, sandbox environments, rate limits.
4. **Ecosystem readiness:** Pre-existing community or official Model Context Protocol (MCP) servers, existing Composio toolkits.
5. **Toolkit buildability verdict:** Green (ready to build today), Yellow (buildable with partner/review caveats or per-instance hosting), Red (unsupported/blocked).
6. **Grounding & Evidence:** Every factual assertion must be anchored in verified documentation URLs with verbatim quote excerpts.

### Pipeline Architecture
- **Phase 0 (Bootstrap):** Project scaffold, git repository, dependency management, API key verification, GitHub Pages and Actions setup.
- **Phase 1 (Schema & Dataset):** Strictly typed Pydantic models with `{value, evidence_url, evidence_quote, confidence}` tuples for all factual claims; seed dataset `data/apps.csv` generated from Appendix A.
- **Phase 2 (Agent Passes 1 & 2):**
  - *Pass 1 (Baseline):* Zero-shot / single-search baseline establishing initial accuracy without advanced retrieval.
  - *Pass 2 (Multi-Angle Pipeline):* Asynchronous multi-query discovery (auth, access, pricing, MCP, review), resilient cached fetching with JS fallbacks, official MCP registry / GitHub search, Composio toolkit catalog matching, and schema-constrained LLM extraction.
- **Phase 3 (Verification & Human Review Queue):**
  - Evidence text validation against cached HTML/markdown.
  - Independent second-model verification (re-extracting on contradiction).
  - Self-consistency voting across critical categorical dimensions.
  - Deterministic rule-based checks (e.g., OAuth without token endpoint, Green buildability with partner gates).
  - Composio integration: pushing low-confidence / conflicting rows to review queue (Google Sheets / CSV).
- **Phase 4 (Accuracy Benchmarking):**
  - Stratified 30-app gold dataset (12 tuning, 18 hold-out).
  - Strict hold-out evaluation measuring progression from Pass 1 through Pass 4.
  - Error taxonomy & root-cause analysis (stale docs, marketing contradictions, entity ambiguity).
- **Phase 5 (Pattern & Strategic Analysis):**
  - Statistical aggregation of auth dominance, access models, blocker distributions, and high-ROI easy wins vs outreach-gated platforms.
  - Formulaic priority scoring for toolkit roadmap.
- **Phase 6 & 7 (Deliverables & Deployment):**
  - Self-contained, responsive, dark/light mode interactive case study at `site/index.html`.
  - Automated deployment via GitHub Pages and interactive GitHub Actions workflow for single-app re-runs.

---

## 2. Phase-by-Phase Log

### Phase 0: Bootstrap & Project Setup
- **Date & Time:** 2026-11-23
- **Actions:**
  - Initialized git repository with strict `.gitignore` (`.env`, `cache/`, `__pycache__/`, `.venv/`).
  - Created directory layout (`data/`, `cache/`, `agent/`, `analysis/`, `site/`, `.github/workflows/`).
  - Created `.env.example` defining environment variables.
  - Authenticated GitHub CLI with user `Sushanth-xy`.

### Phase 1: Schema Architecture & Dataset Seeding
- **Date & Time:** 2026-11-23
- **Actions:**
  - Authored `data/apps.csv` containing all 100 applications categorized from Appendix A.
  - Implemented `agent/schema.py` utilizing strict Pydantic models.
  - Standardized all factual fields into `{value, evidence_url, evidence_quote, confidence}` tuples.
  - Validated dry-run serialization and enum constraints against sample app (Attio).

### Phase 2: Agent Baseline (Pass 1) & Multi-Angle Grounded Pipeline (Pass 2)
- **Model Selection & Rate Limit Engineering:**
  - Evaluated current Gemini models: `gemini-3.5-flash-lite` selected as primary extraction engine due to high speed and low latency.
  - Identified Gemini Free Tier quota ceiling of 15 Requests Per Minute (15 RPM).
  - Implemented thread-safe token bucket rate limiter in `agent/extract.py` with `MIN_INTERVAL = 4.2s` and exponential backoff retry.
  - Added multi-model fallback cascade (`gemini-3.5-flash`, `gemini-3.1-flash-lite`) if primary model is saturated.
- **Extraction Hardening:**
  - Discovered edge cases in LLM outputs where `estimated_tool_count` was returned as a scalar integer rather than a dictionary. Implemented `_sanitize_record_dict()` in `agent/extract.py` to auto-normalize fields.
  - Added `"unknown"` to `AuthMethod` and `ExistingMcpType` literals to handle apps with unstated auth/MCP details without raising Pydantic validation errors.
- **Pass 1 Execution:**
  - Ran baseline zero-shot extraction across all 100 apps.
  - Saved to `data/results_pass1.jsonl`.
- **Pass 2 Execution:**
  - Executed 5 targeted search queries per app (`API authentication`, `getting started API credentials`, `pricing plans access`, `OAuth app review`, `rate limits openapi`).
  - Fetched and cached official documentation pages by SHA256(URL).
  - Queried official GitHub repositories and Composio catalog.
  - Generated grounded citations with verbatim quotes.

- **Search Provider Fallback (Tavily Quota Protection):**
  - Received user notification of 80% Tavily credit consumption.
  - Immediately transitioned primary discovery search to DuckDuckGo HTML parser and cached vendor hint URLs via `httpx`.
  - Zero additional Tavily API calls dispatched, preserving user quota while maintaining grounded evidence collection.

### Phase 3: Verification Loops & Review Queue Triage
- **Verification Loop Implementation:**
  - *Evidence Grounding Loop:* Verified whether extracted quotes exist verbatim (or >80% token match) in cached page texts.
  - *Deterministic Rule Invariants:* Evaluated logical contradictions across fields (e.g. Green buildability paired with fatal blockers like partner gating; CLI tools misclassified as SaaS; unverified official MCP servers).
  - *Disambiguation Checks:* Flagged high-risk brand collisions (Pumble, fanbasis, Paygent Connect, Consensus, higgsfield).
  - Flags and low-confidence rows routed to review queue (20 items flagged).
- **Composio SDK Middle Path Integration Attempt & Fallback:**
  - Implemented Google Sheets export via `composio` SDK (`c.connected_accounts.list()`).
  - Result: API key returned `composio_client._exceptions.AuthenticationError: 401 Invalid API key: ck_**oBk6` from `https://backend.composio.dev`.
  - Fallback executed as specified in brief: All 20 flagged review items exported to `data/review.csv` with evidence links and rationale. Documented honestly on case study page.
- **Search Fallback Impact on Pass 2:**
  - After app 55, live Tavily API calls were suspended due to 80% usage threshold.
  - The remaining 45 apps utilized local disk cache, direct vendor seed URL fetching (`httpx`), and DuckDuckGo HTML queries.
  - Pass 2 quote verification rate: Apps 1-55 (Tavily) verified at 94.9% (478/504), Apps 56-100 (DDG + cache) verified at 95.4% (388/407). Overall: 95.1% across 911 total factual claims.
- **Repository Security Audit:**
  - Confirmed `.env` and `cache/` were never committed anywhere in git history (`git log --all --full-history -- ".env" "cache/*"` returned zero results).

### Phase 3 Review & Human Checkpoint 1 Corrections
- **Human Interventions & Corrections:**
  - **Fathom (ID 93):** `agent wrong, human right, root cause: only searched marketing/support/docs pages, missed vendor developer portal / vendor GitHub org.` Corrected from `red` (`no_public_api`) to `green` (`self_serve_free`) with REST API, API key (`X-Api-Key`) + OAuth2, and official MCP server hosted at `api.fathom.ai/mcp`.
  - **Xero (ID 87):** `agent wrong, human right, root cause: only searched marketing/support/docs pages, missed vendor developer portal / vendor GitHub org.` Corrected from `community` to `official` MCP server hosted at `github.com/XeroAPI/xero-mcp-server` (vendor-owned GitHub organization).
  - **MCP Definition Standardization:** Relaxed overly strict "vendor-owned GitHub repo" rule to `official = vendor-documented or vendor-owned; community = third-party`. Verified official hosted MCP servers for Monday.com (`developer.monday.com/api-reference/docs/mondaycom-mcp`), ClickUp (`developer.clickup.com/docs/connect-an-ai-assistant-to-clickups-mcp-server`), Smartsheet (`developers.smartsheet.com/ai-mcp/smartsheet/mcp-server-tools`), Plaid (`github.com/plaid/ai-coding-toolkit`), and LiveAgent (`github.com/QualityUnit/liveagent-mcp-server`).
  - **CLI Heuristic Regex Bug Fix:** Corrected substring match `"cli"` in `agent/verify.py` to whole-word regex `\bcli\b`. Zoho Cliq and ClickUp were the only two apps falsely flagged by the heuristic. Both confirmed as `hosted_saas`.
  - **Unified CLI Tool Policy:** Standardized policy across all 3 CLI tools (Sherlock #58, higgsfield #97, Mermaid CLI #98) to `yellow` with `main_blocker = cli_or_local_only`, since CLI tools require sandboxed container runtime execution rather than remote OAuth/REST endpoints.
  - **Entity Disambiguation:**
    - *Paygent Connect (ID 84):* Re-checked NMI entity; no public documentation exists under Paygent Connect. Marked `unclear`, `yellow`, `thin_or_unclear_docs` with `low` confidence.
    - *fanbasis (ID 50):* Creator monetization platform without public developer API -> `red`, `no_public_api`, labeled as absence finding.
    - *Consensus (ID 94):* Academic AI search engine requiring private pilot OAuth partner request -> `yellow`, `partner_gated`, labeled as absence finding.
    - *YouTube Transcript (ID 99) & Grain (ID 100):* Fetched official developer documentation (`transcriptapi.com/docs/api/` and `developers.grain.com`); both confirmed `green`, `self_serve_free`.
  - **Verbatim Quote Hardening:** Re-fetched and cached exact pages for Salesforce (ID 1), Twilio (ID 22), Meta Ads (ID 32), and Netlify (ID 63). Confirmed 100% exact substring match in local disk cache. All non-quote absence findings labeled explicitly as `Absence finding: ...`.

### Phase 4: Accuracy Benchmarking & Hold-Out Evaluation
- **Dataset Splitting:**
  - 30-app stratified sample (3 apps per category across all 10 categories).
  - Deliberately covers 6 obscure apps (Pumble, DealCloud, Waterfall.io, fanbasis, Gladly, Paygent Connect), 4 approval-gated platforms (Google Ads, Meta Ads, Amazon SP-API, PitchBook), 3 CLI tools (Sherlock, higgsfield, Mermaid CLI), and industry-standard reference APIs (Stripe, GitHub, Shopify, HubSpot).
  - Split: 12 tuning apps vs 18 strict hold-out apps. Prompts and heuristics were never tuned against hold-out.
  - `data/gold_template.csv` authored with 100% empty answer fields to prevent LLM anchoring.
- **Accuracy Progression:**
  - **Pass 1 (Zero-Shot Baseline):**
    - Tuning Accuracy: 66.7%
    - Hold-Out Accuracy: 66.7%
    - Overall Sample Accuracy: 66.7%
  - **Pass 2 (Multi-Angle Pipeline):**
    - Tuning Accuracy: 75.7% (+9.0%)
    - Hold-Out Accuracy: 66.7%
    - Overall Sample Accuracy: 70.3% (+3.6%)
  - **Pass 3 (Verification Loops):**
    - Tuning Accuracy: 75.7%
    - Hold-Out Accuracy: 66.7%
    - Overall Sample Accuracy: 70.3%
  - **Pass 4 (Final with Human Audit):**
    - Tuning Accuracy: 75.7%
    - Hold-Out Accuracy: 70.4% (+3.7% jump on unseen hold-out)
    - Overall Sample Accuracy: 72.5% (+5.8% over baseline)
- **Root-Cause Error Taxonomy:**
  1. *Subdomain Obscurity / Portal Misses:* Developer portals hosted on separate domains (`developers.*`, `api.*`) or GitHub orgs (`XeroAPI/xero-mcp-server`) missed by top-level marketing searches.
  2. *Strict vs Permissive Gating Definitions:* Gating differences between self-serve sandbox API access vs production managed OAuth app distribution (e.g. Meta Ads, Google Ads).
  3. *CLI vs HTTP Runtime Mismatch:* CLI-only tools requiring container execution flagged as missing REST APIs before skill-wrapping policy was established.
  4. *Entity Collision:* Ambiguous brand names (Paygent Connect vs Japanese Paygent Co; iPayX legacy payment gateway vs ai protocols).

### Phase 5: Pattern & Strategic Analysis
- 54.0% of target apps rely on OAuth2 (54/100), but over 36% gate managed OAuth distribution behind app review or developer agreements.
- 74.0% offer immediate self-serve developer access (74/100), representing quick-win toolkit opportunities.
- 66 apps are greenlit for immediate toolkit development (`green`), 30 require per-instance configuration or partner approval (`yellow`), and 4 are blocked (`red`).

