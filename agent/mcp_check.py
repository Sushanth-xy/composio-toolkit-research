"""MCP check and Composio catalog verification module.

Checks for:
1. Existing Model Context Protocol (MCP) servers (official vs community)
2. Whether Composio already has a toolkit for this application
"""

import os
import httpx
from typing import Tuple, Optional
from agent.search import search_web

# Known apps already supported in Composio's public toolkit catalog (https://docs.composio.dev/toolkits)
KNOWN_COMPOSIO_APPS = {
    "salesforce", "hubspot", "pipedrive", "attio", "zoho crm", "close", "copper",
    "zendesk", "intercom", "freshdesk", "front", "help scout", "gorgias",
    "slack", "twilio", "discord", "telegram", "whatsapp business", "aircall",
    "google ads", "meta ads", "mailchimp", "klaviyo", "sendgrid",
    "shopify", "woocommerce", "bigcommerce", "gumroad",
    "apify", "firecrawl", "bright data",
    "github", "vercel", "netlify", "cloudflare", "supabase", "snowflake", "mongodb atlas", "datadog", "sentry",
    "notion", "airtable", "linear", "jira", "asana", "monday.com", "clickup", "coda", "smartsheet", "harvest",
    "stripe", "plaid", "quickbooks", "xero", "brex", "ramp",
    "fathom",
}


def check_already_in_composio(app_name: str) -> str:
    """Check if app is already available in Composio's catalog."""
    norm = app_name.strip().lower()
    if norm in KNOWN_COMPOSIO_APPS:
        return "yes"
    for k in KNOWN_COMPOSIO_APPS:
        if k in norm or norm in k:
            return "yes"
    return "no"


def check_existing_mcp(app_name: str, hint: str = "") -> Tuple[str, Optional[str]]:
    """Check if an MCP server exists for this application.
    
    Returns (status, mcp_url) where status in ('official', 'community', 'none').
    """
    query = f"{app_name} model context protocol mcp server github"
    results = search_web(query, max_results=5)

    official_candidates = []
    community_candidates = []

    # Extract hint domain for official repo matching
    clean_hint = hint.split()[0].replace("https://", "").replace("http://", "").split("/")[0]

    for r in results:
        url = r.get("url", "")
        title = r.get("title", "").lower()
        content = r.get("content", "").lower()
        combined = f"{title} {content}"

        if "mcp" not in combined:
            continue

        if "github.com/" in url:
            # Check if vendor official
            parts = url.split("github.com/")[-1].split("/")
            if len(parts) >= 2:
                owner = parts[0].lower()
                repo = parts[1].lower()
                
                # Check if official vendor repo or official modelcontextprotocol repo
                is_vendor_org = (
                    app_name.lower().replace(" ", "").replace("-", "") in owner
                    or (clean_hint and clean_hint.split(".")[0] in owner)
                )
                if is_vendor_org:
                    official_candidates.append(url)
                elif "mcp" in repo:
                    community_candidates.append(url)

    if official_candidates:
        return "official", official_candidates[0]
    elif community_candidates:
        return "community", community_candidates[0]

    return "none", None
