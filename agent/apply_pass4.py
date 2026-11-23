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

    # 1. Salesforce (ID 1) - Re-verified exact doc quote
    r1 = records[1]
    r1.access_model = Fact(
        value="self_serve_free",
        evidence_url="https://docs.unified.to/guides/how_to_register_a_salesforce_developer_app_and_get_oauth_2_credentials",
        evidence_quote="By registering a developer app, you can generate a client ID and a client secret, which are the credentials you'll need to authenticate your requests to the Salesforce APIs",
        confidence="high"
    )
    r1.overall_confidence = "high"

    # 2. Twilio (ID 22) - Re-verified exact doc quote
    r22 = records[22]
    r22.access_model = Fact(
        value="self_serve_trial",
        evidence_url="https://www.twilio.com/docs/usage/api",
        evidence_quote="With the Twilio APIs, you can build applications that help your users send messages, make phone calls, look up phone numbers, and more.",
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

    # 3. LiveAgent (ID 16) - QualityUnit is the vendor org
    r16 = records[16]
    r16.existing_mcp = ExistingMcpFact(
        value="official",
        mcp_url="https://github.com/QualityUnit/liveagent-mcp-server",
        evidence_url="https://github.com/QualityUnit/liveagent-mcp-server",
        evidence_quote="GitHub - QualityUnit/liveagent-mcp-server: LiveAgent MCP Server to automate tasks in your helpdesk · GitHub",
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

    # 5. Meta Ads (ID 32) - Re-verified exact doc quote
    r32 = records[32]
    r32.access_model = Fact(
        value="app_review_required",
        evidence_url="https://unified.to/blog/how_to_get_your_meta_ads_api_key",
        evidence_quote="Step 4: App Review and Business Verification (for production)",
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

    # 7. Sherlock (ID 58) - Consistent CLI policy -> yellow
    r58 = records[58]
    r58.buildability = Fact(
        value="yellow",
        evidence_url="https://github.com/sherlock-project/sherlock",
        evidence_quote="GitHub - sherlock-project/sherlock: Hunt down social media accounts by username across social networks · GitHub",
        confidence="high"
    )
    r58.main_blocker = Fact(
        value="cli_or_local_only",
        evidence_url="https://github.com/sherlock-project/sherlock",
        evidence_quote="GitHub - sherlock-project/sherlock: Hunt down social media accounts by username across social networks · GitHub",
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

    # 12. Plaid (ID 82) - Official repo on vendor GitHub org
    r82 = records[82]
    r82.existing_mcp = ExistingMcpFact(
        value="official",
        mcp_url="https://github.com/plaid/ai-coding-toolkit",
        evidence_url="https://github.com/plaid/ai-coding-toolkit",
        evidence_quote="Build your Plaid integration in record time with a development toolkit for your AI coding tools, including prompts, sandbox data, and an MCP server.",
        confidence="high"
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

    # 14. iPayX (ID 85) - Defunct / unreachable domain
    r85 = records[85]
    r85.buildability = Fact(
        value="red",
        evidence_url="https://www.ipayx.com",
        evidence_quote="Absence finding: Defunct/unreachable domain ipayx.com; no public developer API exists.",
        confidence="high"
    )
    r85.main_blocker = Fact(
        value="no_public_api",
        evidence_url="https://www.ipayx.com",
        evidence_quote="Absence finding: Defunct/unreachable domain ipayx.com; no public developer API exists.",
        confidence="high"
    )
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

    # 18. higgsfield (ID 97) - Consistent CLI policy -> yellow
    r97 = records[97]
    r97.app_type = Fact(
        value="cli_tool",
        evidence_url="https://higgsfield.ai",
        evidence_quote="Run Blender, creative apps and your own LoRAs through MCP",
        confidence="high"
    )
    r97.api_type = Fact(
        value=["cli_only"],
        evidence_url="https://higgsfield.ai",
        evidence_quote="Run Blender, creative apps and your own LoRAs through MCP",
        confidence="high"
    )
    r97.buildability = Fact(
        value="yellow",
        evidence_url="https://higgsfield.ai",
        evidence_quote="Run Blender, creative apps and your own LoRAs through MCP",
        confidence="high"
    )
    r97.main_blocker = Fact(
        value="cli_or_local_only",
        evidence_url="https://higgsfield.ai",
        evidence_quote="Run Blender, creative apps and your own LoRAs through MCP",
        confidence="high"
    )
    r97.overall_confidence = "high"

    # 19. Mermaid CLI (ID 98) - Consistent CLI policy -> yellow
    r98 = records[98]
    r98.buildability = Fact(
        value="yellow",
        evidence_url="https://github.com/mermaid-js/mermaid-cli",
        evidence_quote="GitHub - mermaid-js/mermaid-cli: Command line tool for the Mermaid library · GitHub",
        confidence="high"
    )
    r98.main_blocker = Fact(
        value="cli_or_local_only",
        evidence_url="https://github.com/mermaid-js/mermaid-cli",
        evidence_quote="GitHub - mermaid-js/mermaid-cli: Command line tool for the Mermaid library · GitHub",
        confidence="high"
    )
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
