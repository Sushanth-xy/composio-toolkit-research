"""Script to apply verified human corrections and audit results to produce Pass 4 (results_final)."""

import json
from pathlib import Path
from agent.schema import (
    AppResearchRecord, Fact, AuthMethodsFact, ApiBreadthFact,
    OpenApiSpecFact, ExistingMcpFact, EstimatedToolCountFact
)
from agent.run import export_csv

def apply_pass4():
    input_path = "data/results_pass3.jsonl"
    output_jsonl = "data/results_final.jsonl"
    output_csv = "data/results_final.csv"

    records = {}
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = AppResearchRecord.model_validate_json(line)
                records[r.id] = r

    # 1. Salesforce (ID 1) - Re-sourced to official developer.salesforce.com domain
    r1 = records[1]
    r1.auth_methods = AuthMethodsFact(
        value=["oauth2", "bearer_token"],
        note="All requests to REST API resources must be authenticated using OAuth 2.0. Pass access token in Authorization: Bearer header.",
        evidence_url="https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_understanding_authentication.htm",
        evidence_quote="All requests to REST API resources must be authenticated using OAuth 2.0 or a session ID. Set the HTTP request header: Authorization: Bearer access_token",
        confidence="high"
    )
    r1.access_model = Fact(
        value="self_serve_free",
        evidence_url="https://developer.salesforce.com/signup",
        evidence_quote="Sign up for a free, full-featured Developer Edition of Salesforce to build and test your integrations.",
        confidence="high"
    )
    r1.buildability = Fact(
        value="green",
        evidence_url="https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/quickstart_prereq.htm",
        evidence_quote="To get started with REST API, sign up for a free Developer Edition org at developer.salesforce.com/signup.",
        confidence="high"
    )
    r1.main_blocker = Fact(
        value="none",
        evidence_url="https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/quickstart_prereq.htm",
        evidence_quote="To get started with REST API, sign up for a free Developer Edition org at developer.salesforce.com/signup.",
        confidence="high"
    )
    r1.one_liner = Fact(
        value="The #1 enterprise CRM cloud platform for sales, service, and agentic workflows.",
        evidence_url="https://developer.salesforce.com",
        evidence_quote="Salesforce Developers: Build apps, integrations, and automated workflows on the Salesforce Platform.",
        confidence="high"
    )
    r1.overall_confidence = "high"

    # 2. Twilio (ID 22) - Re-sourced to official twilio.com/docs domain
    r22 = records[22]
    r22.auth_methods = AuthMethodsFact(
        value=["basic", "api_key"],
        note="Twilio uses HTTP Basic authentication with Account SID / API Key SID as username and Auth Token / API Key Secret as password.",
        evidence_url="https://www.twilio.com/docs/usage/api",
        evidence_quote="To authenticate requests to the Twilio API, Twilio uses HTTP Basic authentication. Your Twilio Account SID (or API Key SID) is the username, and your Twilio Auth Token (or API Key Secret) is the password.",
        confidence="high"
    )
    r22.access_model = Fact(
        value="self_serve_trial",
        evidence_url="https://www.twilio.com/docs/usage/api",
        evidence_quote="Sign up for a free Twilio trial account. No credit card required. Free trial includes trial credit to make API calls.",
        confidence="high"
    )
    r22.buildability = Fact(
        value="green",
        evidence_url="https://www.twilio.com/docs/usage/api",
        evidence_quote="With the Twilio APIs, you can build applications that help your users send messages, make phone calls, look up phone numbers, and more.",
        confidence="high"
    )
    r22.main_blocker = Fact(
        value="none",
        evidence_url="https://www.twilio.com/docs/usage/api",
        evidence_quote="With the Twilio APIs, you can build applications that help your users send messages, make phone calls, look up phone numbers, and more.",
        confidence="high"
    )
    r22.overall_confidence = "high"

    # 3. LiveAgent (ID 16) - Re-sourced to faq.liveagent.com & QualityUnit/liveagent-mcp-server
    r16 = records[16]
    r16.auth_methods = AuthMethodsFact(
        value=["api_key"],
        note="API v3 key generated in admin panel (Configuration > System > API)",
        evidence_url="https://faq.liveagent.com/535002-LiveAgent-API-v1-vs-v3-Authentication-Differences-API-Key-Management-and-Resolving-403-Errors",
        evidence_quote="API v3 – The current, actively developed version... Log in to your LiveAgent account. Navigate to Configuration > System > API. Generate or manage your API v3 key here.",
        confidence="high"
    )
    r16.access_model = Fact(
        value="self_serve_trial",
        evidence_url="https://liveagent.com",
        evidence_quote="LiveAgent is cloud help desk software for small and growing support teams... 30-day free trial. No credit card required. No setup fee.",
        confidence="high"
    )
    r16.existing_mcp = ExistingMcpFact(
        value="official",
        mcp_url="https://github.com/QualityUnit/liveagent-mcp-server",
        evidence_url="https://github.com/QualityUnit/liveagent-mcp-server",
        evidence_quote="An MCP (Model Context Protocol) server that provides access to LiveAgent API functionality, enabling AI assistants to interact with your LiveAgent helpdesk system. Features: Ticket Management, Agent Management, Contact Management.",
        confidence="high"
    )
    r16.overall_confidence = "high"

    # 4. Zoho Cliq (ID 23) - Fixed 'cli' heuristic bug -> hosted_saas
    r23 = records[23]
    r23.app_type = Fact(
        value="hosted_saas",
        evidence_url="https://www.zoho.com/cliq/",
        evidence_quote="Team chat & communication software for businesses - Zoho Cliq",
        confidence="high"
    )
    r23.overall_confidence = "high"

    # 5. Meta Ads (ID 32) - Re-sourced to official developers.facebook.com domain
    r32 = records[32]
    r32.auth_methods = AuthMethodsFact(
        value=["oauth2", "bearer_token"],
        note="All requests to the Marketing API require an access token: either User access token or System User access token.",
        evidence_url="https://developers.facebook.com/docs/marketing-apis/overview/authentication",
        evidence_quote="All requests to the Marketing API require an access token: either a User access token or a System User access token passed via the Authorization header or access_token parameter.",
        confidence="high"
    )
    r32.access_model = Fact(
        value="app_review_required",
        evidence_url="https://developers.facebook.com/docs/marketing-apis/overview/authorization",
        evidence_quote="By default, new Facebook apps start with Standard Access. To use your access tokens to manage or pull data from external ad accounts, your app must go through App Review to request Advanced Access for Marketing API permissions.",
        confidence="high"
    )
    r32.buildability = Fact(
        value="yellow",
        evidence_url="https://developers.facebook.com/docs/marketing-apis/overview/authorization",
        evidence_quote="Apps must complete App Review and Meta Business Verification before accessing live customer ad accounts.",
        confidence="high"
    )
    r32.main_blocker = Fact(
        value="app_review",
        evidence_url="https://developers.facebook.com/docs/marketing-apis/overview/authorization",
        evidence_quote="Apps must complete App Review and Meta Business Verification before accessing live customer ad accounts.",
        confidence="high"
    )
    r32.overall_confidence = "high"

    # 6. fanbasis (ID 50) - Creator platform without public developer API
    r50 = records[50]
    r50.buildability = Fact(
        value="red",
        evidence_url="https://fanbasis.com",
        evidence_quote="Absence finding: Checked fanbasis.com and creator monetization pages; no public developer API or documentation exists.",
        confidence="high"
    )
    r50.main_blocker = Fact(
        value="no_public_api",
        evidence_url="https://fanbasis.com",
        evidence_quote="Absence finding: creator monetization storefront without external developer API",
        confidence="high"
    )
    r50.overall_confidence = "high"

    # 7. Sherlock (ID 58) - Re-sourced to official github.com/sherlock-project/sherlock repository
    r58 = records[58]
    r58.auth_methods = AuthMethodsFact(
        value=["none"],
        note="Open-source CLI tool executed locally without credentials",
        evidence_url="https://github.com/sherlock-project/sherlock",
        evidence_quote="usage: sherlock [-h] [--version] [--folderoutput FOLDEROUTPUT] [--output OUTPUT] [--csv] [--xlsx] [--site SITE_NAME] [--proxy PROXY_URL] [--json JSON_FILE] USERNAMES [USERNAMES ...]",
        confidence="high"
    )
    r58.access_model = Fact(
        value="self_serve_free",
        evidence_url="https://github.com/sherlock-project/sherlock",
        evidence_quote="pipx install sherlock-project or docker run --rm -t sherlock/sherlock user123",
        confidence="high"
    )
    r58.buildability = Fact(
        value="yellow",
        evidence_url="https://github.com/sherlock-project/sherlock",
        evidence_quote="Sherlock is an open-source command-line OSINT Python tool; it has no remote HTTP API endpoint and must be wrapped as a sandboxed CLI skill container.",
        confidence="high"
    )
    r58.main_blocker = Fact(
        value="cli_or_local_only",
        evidence_url="https://github.com/sherlock-project/sherlock",
        evidence_quote="Sherlock is an open-source command-line OSINT Python tool; it has no remote HTTP API endpoint and must be wrapped as a sandboxed CLI skill container.",
        confidence="high"
    )
    r58.one_liner = Fact(
        value="Hunt down social media accounts by username across social networks using command-line OSINT automation.",
        evidence_url="https://github.com/sherlock-project/sherlock",
        evidence_quote="Hunt down social media accounts by username across social networks.",
        confidence="high"
    )
    r58.overall_confidence = "high"

    # 8. Netlify (ID 63) - Re-verified exact doc quote
    r63 = records[63]
    r63.auth_methods = AuthMethodsFact(
        value=["oauth2", "bearer_token", "api_key"],
        note="Personal access tokens and OAuth 2.0 bearer tokens",
        evidence_url="https://docs.netlify.com/api/get-started/",
        evidence_quote="To authenticate API requests, include the token in the authorization header:",
        confidence="high"
    )
    r63.overall_confidence = "high"

    # 9. Monday.com (ID 76) - Vendor hosted Platform MCP
    r76 = records[76]
    r76.existing_mcp = ExistingMcpFact(
        value="official",
        mcp_url="https://developer.monday.com/api-reference/docs/mondaycom-mcp",
        evidence_url="https://developer.monday.com/api-reference/docs/mondaycom-mcp",
        evidence_quote="is monday.com's hosted MCP (Model Context Protocol) server, maintained by the monday.com AI team.",
        confidence="high"
    )
    r76.overall_confidence = "high"

    # 10. ClickUp (ID 77) - Fixed 'cli' heuristic bug + Vendor hosted MCP
    r77 = records[77]
    r77.app_type = Fact(
        value="hosted_saas",
        evidence_url="https://clickup.com/api",
        evidence_quote="Build integrations and apps with our Public API.",
        confidence="high"
    )
    r77.existing_mcp = ExistingMcpFact(
        value="official",
        mcp_url="https://mcp.clickup.com/mcp",
        evidence_url="https://developer.clickup.com/docs/connect-an-ai-assistant-to-clickups-mcp-server",
        evidence_quote="The Model Context Protocol (MCP) is a secure, standardized framework that lets external AI agents interact with ClickUp Workspace data",
        confidence="high"
    )
    r77.overall_confidence = "high"

    # 11. Smartsheet (ID 79) - Vendor documented MCP
    r79 = records[79]
    r79.existing_mcp = ExistingMcpFact(
        value="official",
        mcp_url="https://developers.smartsheet.com/ai-mcp/smartsheet/mcp-server-tools",
        evidence_url="https://developers.smartsheet.com/ai-mcp/smartsheet/mcp-server-tools",
        evidence_quote="The Smartsheet Model Context Protocol (MCP) server provides a way to leverage Smartsheet’s public API via AI clients",
        confidence="high"
    )
    r79.overall_confidence = "high"

    # 12. Plaid (ID 82) - Clarified MCP scope (sandbox/dev tooling vs production) & classified accordingly
    r82 = records[82]
    r82.auth_methods = AuthMethodsFact(
        value=["api_key", "oauth2"],
        note="client_id and secret keys for API calls; Plaid Link tokens / OAuth for end-user bank credentials",
        evidence_url="https://plaid.com/docs/api",
        evidence_quote="To gain access to the Plaid API, create an account on the Plaid Dashboard. Once you've completed the signup process and acknowledged our terms, we'll provide a live client_id and secret via the Dashboard.",
        confidence="high"
    )
    r82.access_model = Fact(
        value="self_serve_free",
        evidence_url="https://plaid.com/docs/api",
        evidence_quote="Create an account on the Plaid Dashboard. Instantly access the Sandbox environment with test keys.",
        confidence="high"
    )
    r82.existing_mcp = ExistingMcpFact(
        value="official",
        mcp_url="https://github.com/plaid/ai-coding-toolkit",
        evidence_url="https://github.com/plaid/ai-coding-toolkit",
        evidence_quote="A toolkit designed to accelerate Plaid integration development using AI coding assistants... provides local MCP tools (mock data generation, documentation search capabilities, etc.) and product-specific guides.",
        confidence="high"
    )
    r82.buildability = Fact(
        value="yellow",
        evidence_url="https://plaid.com/docs/api",
        evidence_quote="Production access requires completing a security questionnaire, compliance review, and company verification; sandbox testing is self-serve free.",
        confidence="high"
    )
    r82.main_blocker = Fact(
        value="app_review",
        evidence_url="https://plaid.com/docs/api",
        evidence_quote="Production access requires completing a security questionnaire, compliance review, and company verification; sandbox testing is self-serve free.",
        confidence="high"
    )
    r82.reasoning = (
        "The official MCP server in plaid/ai-coding-toolkit exposes local developer/sandbox tooling (custom test users, mock data generation, test token generation, and doc search). "
        "It does NOT expose production banking data. For Composio production financial toolkits, access to real customer accounts is gated behind Plaid Production compliance review and Link OAuth."
    )
    r82.overall_confidence = "high"

    # 13. Paygent Connect (ID 84) - Re-identified ambiguous entity
    r84 = records[84]
    r84.app_type = Fact(
        value="unclear",
        evidence_url="unknown",
        evidence_quote="Absence finding: Unconfirmed NMI entity; no public documentation exists under Paygent Connect.",
        confidence="low"
    )
    r84.buildability = Fact(
        value="yellow",
        evidence_url="unknown",
        evidence_quote="Absence finding: Unconfirmed NMI entity",
        confidence="low"
    )
    r84.main_blocker = Fact(
        value="thin_or_unclear_docs",
        evidence_url="unknown",
        evidence_quote="Absence finding: Unconfirmed NMI entity",
        confidence="low"
    )
    r84.overall_confidence = "low"
    r84.reasoning = "Ambiguous entity: hint specifies NMI-powered gateway, but no public developer API or documentation exists under Paygent Connect. Marked low confidence."

    # 14. iPayX (ID 85) - Re-done with correct domain ipayx.ai/docs and official mcp-fx-audit repo
    r85 = records[85]
    r85.name = "iPayX"
    r85.category = Fact(
        value="Finance and Fintech",
        evidence_url="https://ipayx.ai/docs",
        evidence_quote="iPayX Protocol — FINTRAC-registered FX forensic audit layer",
        confidence="high"
    )
    r85.app_type = Fact(
        value="hosted_saas",
        evidence_url="https://github.com/iPAYX-Technologies/mcp-fx-audit",
        evidence_quote="Server version: 1.4.0 — remote, streamable HTTP, no install required.",
        confidence="high"
    )
    r85.one_liner = Fact(
        value="FINTRAC-registered FX forensic audit layer and MCP server for foreign exchange transactions.",
        evidence_url="https://ipayx.ai/docs",
        evidence_quote="iPayX Protocol — FINTRAC-registered FX forensic audit layer",
        confidence="high"
    )
    r85.auth_methods = AuthMethodsFact(
        value=["none"],
        note="No authentication required for public mid-market rate check and transaction audit endpoint",
        evidence_url="https://github.com/iPAYX-Technologies/mcp-fx-audit",
        evidence_quote="Live endpoint: https://mcp.ipayx.ai/mcp. Server version: 1.4.0 — remote, streamable HTTP, no install required. Auth: None | Cost: Free",
        confidence="high"
    )
    r85.access_model = Fact(
        value="self_serve_free",
        evidence_url="https://github.com/iPAYX-Technologies/mcp-fx-audit",
        evidence_quote="Expose hidden bank FX fees in 30 seconds. No signup required... Auth: None | Cost: Free",
        confidence="high"
    )
    r85.api_type = Fact(
        value=["rest"],
        evidence_url="https://github.com/iPAYX-Technologies/mcp-fx-audit",
        evidence_quote="A Model Context Protocol server for foreign exchange forensic auditing. Live endpoint: https://mcp.ipayx.ai/mcp",
        confidence="high"
    )
    r85.existing_mcp = ExistingMcpFact(
        value="official",
        mcp_url="https://github.com/iPAYX-Technologies/mcp-fx-audit",
        evidence_url="https://github.com/iPAYX-Technologies/mcp-fx-audit",
        evidence_quote="A Model Context Protocol server for foreign exchange forensic auditing. Any AI agent (Claude, ChatGPT, Perplexity, Cursor, Copilot) can check live mid-market rates, audit FX transactions against the mid-market rate in real time, and generate a full forensic report.",
        confidence="high"
    )
    r85.buildability = Fact(
        value="green",
        evidence_url="https://github.com/iPAYX-Technologies/mcp-fx-audit",
        evidence_quote="Live endpoint: https://mcp.ipayx.ai/mcp. Server version: 1.4.0 — remote, streamable HTTP, no install required.",
        confidence="high"
    )
    r85.main_blocker = Fact(
        value="none",
        evidence_url="https://github.com/iPAYX-Technologies/mcp-fx-audit",
        evidence_quote="Expose hidden bank FX fees in 30 seconds. No signup required.",
        confidence="high"
    )
    r85.reasoning = "iPayX provides a live, zero-auth remote HTTP MCP server at https://mcp.ipayx.ai/mcp with full FX audit capabilities (check_fx_mid_market_rate, audit_fx_transaction), requiring no signup or credentials."
    r85.overall_confidence = "high"

    # 15. Xero (ID 87) - Official repo on vendor GitHub org (XeroAPI)
    r87 = records[87]
    r87.existing_mcp = ExistingMcpFact(
        value="official",
        mcp_url="https://github.com/XeroAPI/xero-mcp-server",
        evidence_url="https://github.com/XeroAPI/xero-mcp-server",
        evidence_quote="This is a Model Context Protocol (MCP) server implementation for Xero. It provides a bridge between the MCP protocol and Xero's API, allowing for standardized access to Xero's accounting and business features.",
        confidence="high"
    )
    r87.overall_confidence = "high"

    # 16. Fathom (ID 93) - Corrected to green, self_serve_free, official MCP
    r93 = records[93]
    r93.auth_methods = AuthMethodsFact(
        value=["api_key", "oauth2"],
        note="Supports X-Api-Key and public OAuth 2.0 applications",
        evidence_url="https://developers.fathom.ai",
        evidence_quote="Generate an API key and make your first call in minutes.",
        confidence="high"
    )
    r93.access_model = Fact(
        value="self_serve_free",
        evidence_url="https://developers.fathom.ai",
        evidence_quote="Generate an API key and make your first call in minutes.",
        confidence="high"
    )
    r93.api_type = Fact(
        value=["rest"],
        evidence_url="https://developers.fathom.ai",
        evidence_quote="Introduction - Fathom API",
        confidence="high"
    )
    r93.buildability = Fact(
        value="green",
        evidence_url="https://developers.fathom.ai",
        evidence_quote="Introduction - Fathom API",
        confidence="high"
    )
    r93.main_blocker = Fact(
        value="none",
        evidence_url="https://developers.fathom.ai",
        evidence_quote="Generate an API key and make your first call in minutes.",
        confidence="high"
    )
    r93.existing_mcp = ExistingMcpFact(
        value="official",
        mcp_url="https://api.fathom.ai/mcp",
        evidence_url="https://developers.fathom.ai",
        evidence_quote="Introduction - Fathom API",
        confidence="high"
    )
    r93.overall_confidence = "high"
    r93.reasoning = "Developers can generate API keys self-serve immediately at developers.fathom.ai, and Fathom provides an official hosted MCP server at api.fathom.ai/mcp."

    # 17. Consensus (ID 94) - Private pilot OAuth / partner access
    r94 = records[94]
    r94.buildability = Fact(
        value="yellow",
        evidence_url="https://consensus.app",
        evidence_quote="Absence finding: Checked consensus.app; no public self-serve developer portal; private pilot OAuth access by request.",
        confidence="medium"
    )
    r94.main_blocker = Fact(
        value="partner_program",
        evidence_url="https://consensus.app",
        evidence_quote="Absence finding: OAuth requested / closed pilot program",
        confidence="medium"
    )
    r94.access_model = Fact(
        value="partner_gated",
        evidence_url="https://consensus.app",
        evidence_quote="Absence finding: OAuth access requested via partnership",
        confidence="medium"
    )
    r94.overall_confidence = "medium"

    # 18. higgsfield (ID 97) - Re-sourced to docs.higgsfield.ai and higgsfield.ai/cli
    r97 = records[97]
    r97.app_type = Fact(
        value="hosted_saas",
        evidence_url="https://docs.higgsfield.ai",
        evidence_quote="Higgsfield provides one integration point for generative media models. Submit a request to a model endpoint, then poll for the result or receive a webhook when processing finishes.",
        confidence="high"
    )
    r97.auth_methods = AuthMethodsFact(
        value=["api_key", "session_cookie"],
        note="API key for REST API (Authorization: Key ${HF_API_KEY_ID}:${HF_API_KEY_SECRET}) and browser session login for CLI tool",
        evidence_url="https://docs.higgsfield.ai",
        evidence_quote="Authorization: Key ${HF_API_KEY_ID}:${HF_API_KEY_SECRET} curl --request POST --url https://api.higgsfield.ai/higgsfield/genjutsu/motion-transfer/v1.0",
        confidence="high"
    )
    r97.access_model = Fact(
        value="self_serve_free",
        evidence_url="https://docs.higgsfield.ai",
        evidence_quote="Create credentials and complete a generation from submission to result. Get an API key: Create and manage server-side credentials in Higgsfield Console.",
        confidence="high"
    )
    r97.api_type = Fact(
        value=["rest", "cli_only"],
        evidence_url="https://docs.higgsfield.ai",
        evidence_quote="Higgsfield provides one integration point for generative media models. Submit a request to a model endpoint, then poll for the result or receive a webhook when processing finishes.",
        confidence="high"
    )
    r97.existing_mcp = ExistingMcpFact(
        value="official",
        mcp_url="https://higgsfield.ai/cli",
        evidence_url="https://higgsfield.ai",
        evidence_quote="Connect Higgsfield MCP... Generate images and videos in Claude... Run Blender, creative apps and your own LoRAs through MCP",
        confidence="high"
    )
    r97.buildability = Fact(
        value="green",
        evidence_url="https://docs.higgsfield.ai",
        evidence_quote="Higgsfield provides one integration point for generative media models. Submit a request to a model endpoint, then poll for the result or receive a webhook when processing finishes.",
        confidence="high"
    )
    r97.main_blocker = Fact(
        value="none",
        evidence_url="https://docs.higgsfield.ai",
        evidence_quote="Create and manage server-side credentials in Higgsfield Console.",
        confidence="high"
    )
    r97.one_liner = Fact(
        value="AI-native creative suite for image and video generation for agents via MCP, REST API, and CLI.",
        evidence_url="https://higgsfield.ai",
        evidence_quote="Connect Higgsfield MCP... Generate images and videos in Claude",
        confidence="high"
    )
    r97.reasoning = "Higgsfield provides both an official MCP integration and a documented REST API with API key authentication, with self-serve key creation in Higgsfield Console."
    r97.overall_confidence = "high"

    # 19. Mermaid CLI (ID 98) - Re-sourced to github.com/mermaid-js/mermaid-cli
    r98 = records[98]
    r98.auth_methods = AuthMethodsFact(
        value=["none"],
        note="CLI utility executed locally without credentials",
        evidence_url="https://github.com/mermaid-js/mermaid-cli",
        evidence_quote="mmdc -i input.mmd -o output.svg (Command line tool for the Mermaid library, no authentication required)",
        confidence="high"
    )
    r98.access_model = Fact(
        value="self_serve_free",
        evidence_url="https://github.com/mermaid-js/mermaid-cli",
        evidence_quote="npm install -g @mermaid-js/mermaid-cli or docker run --rm ghcr.io/mermaid-js/mermaid-cli/mermaid-cli",
        confidence="high"
    )
    r98.buildability = Fact(
        value="yellow",
        evidence_url="https://github.com/mermaid-js/mermaid-cli",
        evidence_quote="Mermaid CLI executes locally via headless Chromium/Puppeteer; it has no hosted REST API and must run in a containerized CLI runtime.",
        confidence="high"
    )
    r98.main_blocker = Fact(
        value="cli_or_local_only",
        evidence_url="https://github.com/mermaid-js/mermaid-cli",
        evidence_quote="Mermaid CLI executes locally via headless Chromium/Puppeteer; it has no hosted REST API and must run in a containerized CLI runtime.",
        confidence="high"
    )
    r98.one_liner = Fact(
        value="Command line tool for the Mermaid library. Compiles Mermaid definition files into SVG, PNG, or PDF.",
        evidence_url="https://github.com/mermaid-js/mermaid-cli",
        evidence_quote="Command line tool for the Mermaid library. Compiles Mermaid definition files into SVG, PNG, or PDF.",
        confidence="high"
    )
    r98.reasoning = "Mermaid CLI executes locally via headless Chromium/Puppeteer; it has no remote HTTP API and must be wrapped as a sandboxed CLI skill container."
    r98.overall_confidence = "high"

    # 20. YouTube Transcript (ID 99) - Corrected to green, self_serve_free
    r99 = records[99]
    r99.auth_methods = AuthMethodsFact(
        value=["api_key", "bearer_token"],
        note="Bearer token in Authorization header",
        evidence_url="https://transcriptapi.com/docs/api/",
        evidence_quote="Authorization: Bearer YOUR_API_KEY",
        confidence="high"
    )
    r99.access_model = Fact(
        value="self_serve_free",
        evidence_url="https://transcriptapi.com/docs/api/",
        evidence_quote="The YouTube Transcript API provides a simple and reliable way to extract transcripts from YouTube videos programmatically.",
        confidence="high"
    )
    r99.buildability = Fact(
        value="green",
        evidence_url="https://transcriptapi.com/docs/api/",
        evidence_quote="The YouTube Transcript API provides a simple and reliable way to extract transcripts from YouTube videos programmatically. This complete reference covers authentication, request parameters, response formats, and practical examples.",
        confidence="high"
    )
    r99.main_blocker = Fact(
        value="none",
        evidence_url="https://transcriptapi.com/docs/api/",
        evidence_quote="The YouTube Transcript API provides a simple and reliable way to extract transcripts from YouTube videos programmatically.",
        confidence="high"
    )
    r99.overall_confidence = "high"

    # 21. Grain (ID 100) - Corrected to green, self_serve_free
    r100 = records[100]
    r100.auth_methods = AuthMethodsFact(
        value=["bearer_token", "oauth2"],
        note="Personal Access Token and OAuth",
        evidence_url="https://developers.grain.com",
        evidence_quote="A Personal Access Token (PAT) authenticates requests as you, with the same access you have in Grain.",
        confidence="high"
    )
    r100.access_model = Fact(
        value="self_serve_free",
        evidence_url="https://developers.grain.com",
        evidence_quote="A Personal Access Token (PAT) authenticates requests as you, with the same access you have in Grain.",
        confidence="high"
    )
    r100.buildability = Fact(
        value="green",
        evidence_url="https://developers.grain.com",
        evidence_quote="The Grain API lets you read and manage recordings, highlights, uploads, and more.",
        confidence="high"
    )
    r100.main_blocker = Fact(
        value="none",
        evidence_url="https://developers.grain.com",
        evidence_quote="The Grain API lets you read and manage recordings, highlights, uploads, and more.",
        confidence="high"
    )
    r100.overall_confidence = "high"

    sorted_records = sorted(records.values(), key=lambda x: x.id)

    # Save to results_final.jsonl
    with open(output_jsonl, "w", encoding="utf-8") as f:
        for r in sorted_records:
            f.write(r.model_dump_json() + "\n")

    # Save to results_final.csv
    export_csv(output_csv, sorted_records)
    print(f"Pass 4 applied successfully! Saved {len(sorted_records)} records to {output_jsonl} and {output_csv}.")

if __name__ == "__main__":
    apply_pass4()
