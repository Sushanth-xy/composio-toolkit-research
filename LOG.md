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
