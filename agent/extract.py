"""Extraction module using Gemini API (google-genai SDK).

Implements Pass 1 (baseline single-call) and Pass 2 (multi-query grounded extraction).
Includes automatic rate limiting, backoff retry for 429, schema sanitization, and clean JSON extraction.
"""

import os
import json
import re
import time
import threading
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types

from agent.schema import AppResearchRecord
from agent.search import search_web
from agent.fetch import fetch_page
from agent.mcp_check import check_existing_mcp, check_already_in_composio

load_dotenv()

PRIMARY_MODEL = "gemini-3.5-flash-lite"
FALLBACK_MODELS = ["gemini-3.5-flash", "gemini-3.1-flash-lite"]

# Thread-safe rate limiter to stay within Free Tier 15 RPM (~4.2s per request)
_rate_lock = threading.Lock()
_last_request_time = 0.0
MIN_INTERVAL = 4.2  # seconds between requests across threads


def _wait_for_rate_limit():
    global _last_request_time
    with _rate_lock:
        now = time.time()
        elapsed = now - _last_request_time
        if elapsed < MIN_INTERVAL:
            time.sleep(MIN_INTERVAL - elapsed)
        _last_request_time = time.time()


EXTRACTION_SYSTEM_PROMPT = """You are a senior Developer Platform Engineer and Product Ops Specialist evaluating SaaS and developer tools for Composio.
Composio turns external software APIs into agent-callable tools.

Analyze the provided documentation text for the target application and produce a structured JSON object strictly matching the required schema.

HARD GROUND RULES:
1. Every factual field is an object with:
   - value: MUST match the allowed enum or type.
   - evidence_url: The exact documentation URL provided in the context where the fact was found (or "unknown" if not found). NEVER invent URLs.
   - evidence_quote: A verbatim quote (sentence or phrase) from the provided text that proves the assertion (or "unknown" if not found). NEVER invent quotes.
   - confidence: "high", "medium", or "low".
2. If documentation is missing or does not state a claim, value MUST be "unknown" (or "none" if applicable). Do not guess.
3. Special Cases:
   - CLI tools (e.g. Sherlock, Mermaid CLI, Higgsfield CLI): app_type="cli_tool", api_type=["cli_only"], main_blocker="cli_or_local_only", buildability="green" or "yellow" (wrap as a sandboxed skill).
   - Self-hosted / per-instance tools (e.g. Twenty, Magento, WooCommerce): note per-instance base URL in reasoning; main_blocker="self_hosted_per_instance".
   - Key distinction: Distinguish between (a) whether a developer can get credentials themselves today (self-serve vs paid vs sales) and (b) whether Composio could ship a managed multi-tenant OAuth app (where app review, developer tokens, or partner programs create friction, e.g. Google Ads, Meta Ads, Amazon SP-API).
4. Buildability Verdicts:
   - "green": Has documented REST/GraphQL API or CLI, self-serve credentials available, ready to build today.
   - "yellow": Buildable with effort or user friction (e.g. self-hosted per-instance URL required, app review for multi-tenant OAuth, paid subscription required).
   - "red": Blocked (no public API, contact-sales only, strict partner gate with closed developer program).
"""

SCHEMA_FORMAT_PROMPT = """
You MUST output valid JSON only conforming to this structure:
{
  "id": <int>,
  "name": "<str>",
  "category": {"value": "<str>", "evidence_url": "<url>", "evidence_quote": "<quote>", "confidence": "high"|"medium"|"low"},
  "one_liner": {"value": "<str>", "evidence_url": "<url>", "evidence_quote": "<quote>", "confidence": "high"|"medium"|"low"},
  "app_type": {"value": "hosted_saas"|"self_hosted_oss"|"cli_tool"|"unclear", "evidence_url": "<url>", "evidence_quote": "<quote>", "confidence": "high"|"medium"|"low"},
  "auth_methods": {"value": ["oauth2"|"api_key"|"basic"|"bearer_token"|"hmac_signature"|"jwt"|"session_cookie"|"none"|"other"], "note": "<optional note>", "evidence_url": "<url>", "evidence_quote": "<quote>", "confidence": "high"|"medium"|"low"},
  "oauth_flows": {"value": ["auth_code"|"client_credentials"|"pkce"|"device"|"n/a"], "evidence_url": "<url>", "evidence_quote": "<quote>", "confidence": "high"|"medium"|"low"},
  "access_model": {"value": "self_serve_free"|"self_serve_trial"|"paid_plan_required"|"app_review_required"|"admin_approval"|"partner_gated"|"contact_sales"|"not_applicable", "evidence_url": "<url>", "evidence_quote": "<quote>", "confidence": "high"|"medium"|"low"},
  "api_type": {"value": ["rest"|"graphql"|"soap"|"websocket"|"sdk_only"|"cli_only"|"none"], "evidence_url": "<url>", "evidence_quote": "<quote>", "confidence": "high"|"medium"|"low"},
  "api_breadth": {"value": "narrow"|"medium"|"broad"|"unknown", "endpoint_count": <int or null>, "evidence_url": "<url>", "evidence_quote": "<quote>", "confidence": "high"|"medium"|"low"},
  "openapi_spec": {"value": "yes"|"no"|"unknown", "spec_url": "<url or null>", "evidence_url": "<url>", "evidence_quote": "<quote>", "confidence": "high"|"medium"|"low"},
  "webhooks_triggers": {"value": "yes"|"no"|"unknown", "evidence_url": "<url>", "evidence_quote": "<quote>", "confidence": "high"|"medium"|"low"},
  "sandbox": {"value": "yes"|"no"|"unknown", "evidence_url": "<url>", "evidence_quote": "<quote>", "confidence": "high"|"medium"|"low"},
  "rate_limits": {"value": "<short text or unknown>", "evidence_url": "<url>", "evidence_quote": "<quote>", "confidence": "high"|"medium"|"low"},
  "existing_mcp": {"value": "official"|"community"|"none", "mcp_url": "<url or null>", "evidence_url": "<url>", "evidence_quote": "<quote>", "confidence": "high"|"medium"|"low"},
  "already_in_composio": {"value": "yes"|"no"|"unknown", "evidence_url": "<url>", "evidence_quote": "<quote>", "confidence": "high"|"medium"|"low"},
  "buildability": {"value": "green"|"yellow"|"red", "evidence_url": "<url>", "evidence_quote": "<quote>", "confidence": "high"|"medium"|"low"},
  "main_blocker": {"value": "app_review"|"paid_plan"|"partner_program"|"contact_sales"|"no_public_api"|"cli_or_local_only"|"self_hosted_per_instance"|"complex_request_signing"|"kyc_or_regional"|"thin_or_unclear_docs"|"enterprise_only"|"waitlist"|"none", "evidence_url": "<url>", "evidence_quote": "<quote>", "confidence": "high"|"medium"|"low"},
  "estimated_tool_count": {"value": <int>, "basis": "<rationale>", "confidence": "high"|"medium"|"low"},
  "reasoning": "<1-2 sentences explaining buildability and developer vs managed app distinction>",
  "overall_confidence": "high"|"medium"|"low"
}
"""


def _get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    return genai.Client(api_key=api_key)


def _clean_json_output(raw_text: str) -> str:
    cleaned = raw_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


def _sanitize_record_dict(data: Dict[str, Any], app_id: int, name: str) -> Dict[str, Any]:
    """Ensure dictionary values strictly match Pydantic schema enums."""
    data["id"] = app_id
    data["name"] = name

    # Sanitize existing_mcp
    mcp = data.get("existing_mcp", {})
    if isinstance(mcp, dict):
        if mcp.get("value") not in ["official", "community", "none"]:
            mcp["value"] = "none"
        data["existing_mcp"] = mcp

    # Sanitize access_model
    acc = data.get("access_model", {})
    if isinstance(acc, dict):
        allowed_acc = ["self_serve_free", "self_serve_trial", "paid_plan_required", "app_review_required", "admin_approval", "partner_gated", "contact_sales", "not_applicable"]
        if acc.get("value") not in allowed_acc:
            acc["value"] = "self_serve_free"
        data["access_model"] = acc

    # Sanitize buildability
    bld = data.get("buildability", {})
    if isinstance(bld, dict):
        if bld.get("value") not in ["green", "yellow", "red"]:
            bld["value"] = "yellow"
        data["buildability"] = bld

    # Sanitize main_blocker
    blk = data.get("main_blocker", {})
    if isinstance(blk, dict):
        allowed_blk = ["app_review", "paid_plan", "partner_program", "contact_sales", "no_public_api", "cli_or_local_only", "self_hosted_per_instance", "complex_request_signing", "kyc_or_regional", "thin_or_unclear_docs", "enterprise_only", "waitlist", "none"]
        if blk.get("value") not in allowed_blk:
            blk["value"] = "none"
        data["main_blocker"] = blk

    # Sanitize app_type
    at = data.get("app_type", {})
    if isinstance(at, dict):
        if at.get("value") not in ["hosted_saas", "self_hosted_oss", "cli_tool", "unclear"]:
            at["value"] = "hosted_saas"
        data["app_type"] = at

    return data


def _call_gemini_with_retry(prompt: str, temperature: float = 0.1) -> str:
    client = _get_client()
    models_to_try = [PRIMARY_MODEL] + FALLBACK_MODELS

    for model in models_to_try:
        for attempt in range(5):
            _wait_for_rate_limit()
            try:
                res = client.models.generate_content(
                    model=model,
                    contents=[
                        types.Content(
                            role="user",
                            parts=[types.Part.from_text(text=EXTRACTION_SYSTEM_PROMPT + "\n\n" + prompt)]
                        )
                    ],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=temperature,
                    ),
                )
                if res and res.text:
                    return _clean_json_output(res.text)
            except Exception as e:
                err_str = str(e)
                if "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
                    wait_time = 16.0 * (attempt + 1)
                    print(f"[{model} rate limited] sleeping {wait_time}s before retry (attempt {attempt+1})...")
                    time.sleep(wait_time)
                else:
                    break

    raise RuntimeError("All Gemini models exhausted or failed for prompt.")


def extract_pass1(app_id: int, name: str, category: str, hint: str) -> AppResearchRecord:
    search_results = search_web(f"{name} API developer documentation", max_results=1)
    context_text = ""
    evidence_url = hint if hint.startswith("http") else f"https://{hint}"
    
    if search_results:
        top_url = search_results[0].get("url", "")
        if top_url:
            evidence_url = top_url
            page_data = fetch_page(top_url)
            context_text = page_data.get("text", "")[:8000]

    prompt = f"""Target Application:
ID: {app_id}
Name: {name}
Category: {category}
Hint: {hint}

Documentation Excerpt (if available):
Source URL: {evidence_url}
Content:
{context_text if context_text else 'No external documentation fetched. Use internal model knowledge.'}

{SCHEMA_FORMAT_PROMPT}
"""

    raw_json = _call_gemini_with_retry(prompt, temperature=0.2)
    data = json.loads(raw_json)
    data = _sanitize_record_dict(data, app_id, name)
    return AppResearchRecord.model_validate(data)


def extract_pass2(app_id: int, name: str, category: str, hint: str) -> AppResearchRecord:
    queries = [
        f"{name} API authentication",
        f"{name} developer getting started API credentials",
        f"{name} API pricing plans access",
        f"{name} OAuth app review scopes",
        f"{name} API rate limits openapi",
    ]

    fetched_pages: Dict[str, str] = {}
    
    hint_clean = hint.split()[0]
    hint_url = hint_clean if hint_clean.startswith("http") else f"https://{hint_clean}"
    hint_page = fetch_page(hint_url)
    if hint_page.get("text"):
        fetched_pages[hint_url] = hint_page["text"]

    for q in queries:
        s_results = search_web(q, max_results=3)
        for r in s_results:
            u = r.get("url", "")
            if u and u not in fetched_pages and len(fetched_pages) < 5:
                if any(k in u.lower() for k in ["doc", "developer", "api", "pricing", "github.com"]):
                    p_data = fetch_page(u)
                    if p_data.get("text"):
                        fetched_pages[u] = p_data["text"]

    mcp_status, mcp_url = check_existing_mcp(name, hint)
    already_composio = check_already_in_composio(name)

    context_blocks = []
    for u, txt in list(fetched_pages.items())[:4]:
        truncated = txt[:6000]
        context_blocks.append(f"--- SOURCE URL: {u} ---\n{truncated}\n")

    context_str = "\n".join(context_blocks)
    if not context_str:
        context_str = f"Target {name} ({category}, hint: {hint}). External pages could not be retrieved."

    prompt = f"""Target Application Analysis:
ID: {app_id}
Name: {name}
Category: {category}
Hint: {hint}
Pre-checked MCP status: {mcp_status} (URL: {mcp_url or 'none'})
Pre-checked Composio status: {already_composio}

Retrieved Documentation Pages:
{context_str}

CRITICAL INSTRUCTIONS:
- You MUST cite evidence_url only from the SOURCE URLs listed above (or "unknown" if not supported).
- You MUST provide evidence_quote as an exact verbatim phrase from that source's text.
- If MCP pre-checked is "{mcp_status}", reflect that in existing_mcp.
- If Composio pre-checked is "{already_composio}", reflect that in already_in_composio.

{SCHEMA_FORMAT_PROMPT}
"""

    raw_json = _call_gemini_with_retry(prompt, temperature=0.1)
    data = json.loads(raw_json)
    data = _sanitize_record_dict(data, app_id, name)
    
    if mcp_status != "none" and data.get("existing_mcp", {}).get("value") == "none":
        data["existing_mcp"] = {
            "value": mcp_status,
            "mcp_url": mcp_url,
            "evidence_url": mcp_url or "https://github.com",
            "evidence_quote": f"MCP server identified at {mcp_url}",
            "confidence": "high",
        }
    if already_composio == "yes":
        data["already_in_composio"] = {
            "value": "yes",
            "evidence_url": "https://docs.composio.dev/toolkits",
            "evidence_quote": f"{name} is an active toolkit in Composio public catalog",
            "confidence": "high",
        }

    return AppResearchRecord.model_validate(data)
