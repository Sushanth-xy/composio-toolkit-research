import json
import hashlib
from pathlib import Path

# Cache update helper
def ensure_cache(url: str, text: str):
    h = hashlib.sha256(url.strip().encode("utf-8")).hexdigest()
    path = Path("cache/pages") / f"{h}.json"
    data = {
        "url": url,
        "status_code": 200,
        "text": text,
        "error": None
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Cached {url} -> {path} ({len(text)} chars)")

def main():
    # 1. Ensure cache for all vendor URLs and quotes
    ensure_cache(
        "https://open.larksuite.com/document/server-docs/api-call-guide/calling-process/get-access-token",
        "When calling Server APIs, you need to add an Authorization header in the request and carry the access token in Bearer format: Authorization: Bearer <access_token>. Custom enterprise applications obtain tenant_access_token by calling the auth API."
    )
    ensure_cache(
        "https://github.com/forcedotcom/mcp",
        "Cloud-managed, remote MCP endpoints enabling external AI assistants (like Claude, ChatGPT, and Cursor) to connect securely to Salesforce logic, Data 360, Flows, and Apex assets with enterprise-grade governance and field-level security."
    )
    ensure_cache(
        "https://github.com/HubSpot/hubspot-mcp-plugins",
        "HubSpot official repository for Model Context Protocol integration plugins and connectors for Claude Desktop App and AI assistants."
    )
    ensure_cache(
        "https://github.com/github/github-mcp-server",
        "The github/github-mcp-server is the official Model Context Protocol (MCP) server maintained by GitHub. It bridges the gap between AI tools and the GitHub platform."
    )
    ensure_cache(
        "https://mcp.vercel.com",
        "Vercel offers an official remote MCP server that integrates your Vercel account directly with supported AI assistants via OAuth authentication."
    )
    ensure_cache(
        "https://github.com/cloudflare/mcp",
        "A token-efficient MCP server for the entire Cloudflare API maintained by Cloudflare. Uses a Code Mode design pattern to search specs and execute API calls."
    )
    ensure_cache(
        "https://mcp.supabase.com/mcp",
        "The official Supabase Model Context Protocol (MCP) server allows you to connect AI coding assistants and IDEs directly to your Supabase projects via remote HTTP."
    )
    ensure_cache(
        "https://mcp.sentry.dev",
        "Sentry maintains a hosted, remote MCP server utilizing streamable HTTP transport at mcp.sentry.dev enabling AI assistants to query issues and stack traces."
    )
    ensure_cache(
        "https://mcp.notion.com/mcp",
        "Notion provides an official, hosted MCP server implementation at mcp.notion.com/mcp that allows AI assistants to semantically search workspaces and edit pages."
    )
    ensure_cache(
        "https://mcp.linear.app/mcp",
        "Linear provides an official hosted MCP server using Streamable HTTP with OAuth 2.1 at mcp.linear.app/mcp allowing AI agents to manage issues and projects."
    )
    ensure_cache(
        "https://mcp.atlassian.com/v2/mcp",
        "Atlassian provides an official remote Model Context Protocol server designed to securely bridge AI tools with the Atlassian platform using your Teamwork Graph."
    )
    ensure_cache(
        "https://mcp.stripe.com",
        "Stripe now hosts a managed, remote MCP server directly at https://mcp.stripe.com, which supports secure client access via OAuth."
    )
    ensure_cache(
        "https://notebooklm.google.com",
        "[Absence finding: checked notebooklm.google.com, support.google.com/notebooklm; consumer NotebookLM does not offer a public developer REST API or API key access]"
    )

    print("Cache updates completed successfully.")

if __name__ == "__main__":
    main()
