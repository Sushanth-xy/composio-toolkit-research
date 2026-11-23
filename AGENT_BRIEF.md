# AGENT_BRIEF.md: Composio "AI Product Ops Intern" take-home, do everything

You are an autonomous coding agent (Antigravity CLI). The human has NOT created a repo, a project, or any accounts' worth of setup. You do all of it: create the project folder, git repo, GitHub repo, code, data, analysis, HTML page, deployment, and README. Work phase by phase. Commit after each phase. Stop ONLY at the **[HUMAN]** checkpoints, and when you stop, say exactly what you need in 3 lines or fewer.

Do not ask permission for things you can decide. Decide, log it in `LOG.md`, move on.

---

## 0. The assignment (verbatim essentials, you cannot open the original page)

Context: Composio turns apps into tools that AI agents can call. Before building a toolkit for an app, they research it: what auth it uses, whether there's a self-serve path or it is partner-gated, what the API surface looks like, and whether it can be an MCP server or agent-callable skills. Doing this by hand across hundreds of apps does not scale.

**Task:** Given 100 apps (Appendix A), for each capture:
1. Category and what it does in one line.
2. Auth method(s): OAuth2, API key, Basic, token, or other.
3. Self-serve vs gated: can a developer get credentials themselves for free or on a trial, or does it need a paid plan, admin approval, or a partnership / contact-sales gate.
4. API surface: documented public REST / GraphQL, roughly how broad, and any existing MCP.
5. Buildability verdict: could this be an agent toolkit today, and the main blocker if not.
6. Evidence: the docs URL / article behind each answer.
7. "and more.." (add useful extra columns).

**The point:** find the patterns. Cluster the results and state what patterns you see (which auth dominates, which categories are self-serve vs gated, the most common blocker, where the easy wins are vs what needs outreach). Insight over raw table.

**Do it with an agent, not by hand.** Build an agent/script/pipeline that does the research across all 100. Using Composio's own SDK and MCP is "in the spirit of the role." Explain what it does and where it needed a human.

**Verify accuracy.** Sample the 100, cross-check the agent's answers against real docs by hand, and report where it was right and wrong. Build real verification loops (agent, browser-use, other means) plus human checks. Show how accuracy moved from a lower first pass to a higher one because of those loops. **Accuracy is what matters most.**

**Deliverable:** a single self-explanatory HTML page (case study) a reviewer understands in ~2 minutes with no narration. It must make clear: findings (clean skimmable table/matrix), patterns (up top, plainly stated, the headline), the agent (what was built, where a human was needed), the proof (live link or runnable trigger), and the verification (accuracy on a sample, hits and misses shown honestly). Show both the final output and the process behind it, and make it consumable by both an agent and a human.

**Constraints:** If the agent got things wrong or an app defeated you, say so on the page. Paid or partnership-gated apps: saying so with evidence is the correct finding, not a failure. Budget 6-8 hours; submit early.

**Submit:** (a) live link to the deployed page, (b) link to a public source repo with a short README on how to run the research agent.

---

## 1. Decisions already made (do not revisit)

- Builder: you (Antigravity CLI `agy`).
- Language: Python 3.11+ for the pipeline; plain HTML/CSS/JS for the page (single file, no build step).
- Pipeline LLM: **Gemini API** (`GEMINI_API_KEY`), using the `google-genai` SDK. Run `agy models`/check Google AI docs for current model names; use a strong model for extraction and a **different** model (or at minimum a different prompt and temperature) for the verifier.
- Search: Tavily (`TAVILY_API_KEY`) or Exa, whichever key the human provides. Fetching: Firecrawl (`FIRECRAWL_API_KEY`) with `httpx` fallback, and Playwright for JS-only pages. If a key is missing, fall back (httpx + DuckDuckGo-style search via the search provider you do have) and log it.
- **Composio middle path (required, small but real):** use the Composio Python SDK (`pip install composio`, key `COMPOSIO_API_KEY`) for ONE concrete step: push the human review queue (flagged/low-confidence rows) into a Google Sheet via Composio's Google Sheets toolkit. Secondary option if Sheets auth is a pain: use Composio's GitHub toolkit to search for existing MCP servers per app. **Before writing any Composio code, read https://docs.composio.dev/docs/quickstart and the Python SDK reference at https://docs.composio.dev/reference/sdk-reference/python. Do not rely on memory for SDK calls; the SDK changes.** The Python package is `composio`; provider packages exist (`composio-gemini`, `composio-google`, etc.) if you want to hand Composio tools to the model. Connecting a Google account needs a Connect Link the human clicks (a **[HUMAN]** step). If Composio fails after a fair try, fall back to `review.csv` and say so honestly on the page (what was attempted, what broke).
- Repo: you create it. Use `gh` CLI. Hosting: **GitHub Pages** for the static page (simplest, needs only `gh` auth). The live proof is a GitHub Actions `workflow_dispatch` that runs the agent for one app and publishes the JSON result, plus a documented CLI command. A Vercel/Netlify serverless function is an optional upgrade only if time remains.
- Project name: `composio-toolkit-research`.

---

## 2. Hard ground rules

1. Every factual claim needs `evidence_url` + `evidence_quote` (verbatim from the fetched page). No evidence → value is `"unknown"`. Never guess. Never invent URLs.
2. Cache every fetched page in `cache/` (hash of URL as filename). Reruns must be cheap and reproducible.
3. Secrets: `.env` only. Create `.gitignore` (with `.env`, `cache/`, `__pycache__/`, `.venv/`) and commit it **before** anything else. Provide `.env.example`. Never print or commit keys.
4. Keep `LOG.md`: decisions, prompt versions, failures, every human correction and why. This feeds the page's "where a human was needed" section and the human's interview prep.
5. **Baseline first.** Pass 1 is deliberately plain and is measured before any improvement. Never tune against the hold-out set (see Phase 4).
6. Be honest everywhere. Misses go on the page.
7. Use proper typography in all human-readable page text (’ and “ ” rather than straight quotes in prose); keep straight quotes in code/HTML/JSON syntax.
8. Run long jobs with concurrency (asyncio, ~8), retries with backoff, and resume support (skip apps already done).

---

## 3. Phase 0: Bootstrap (do this immediately, ~20 min)

1. Create `composio-toolkit-research/`, `git init`, add `.gitignore` first, then the layout below.
2. Ask the human **once, in a single message** for the following (a checklist, not a conversation), then continue with what you can while waiting:
   - `GEMINI_API_KEY`
   - `COMPOSIO_API_KEY` (dashboard.composio.dev → Settings → API Keys)
   - `TAVILY_API_KEY` or `EXA_API_KEY`
   - `FIRECRAWL_API_KEY` (optional)
   - Run `gh auth login` (they must do this interactively), and confirm GitHub username.
3. Put keys into `.env` (they paste, or they create the file themselves). Verify each key with a trivial live call; report which work.
4. Create the public GitHub repo with `gh repo create composio-toolkit-research --public --source=. --push` once `gh` is authenticated.

**Layout:**
```
composio-toolkit-research/
  README.md  LOG.md  AGENT_BRIEF.md  .env.example  .gitignore  requirements.txt
  data/        apps.csv  gold.csv  results_pass{1,2,3}.jsonl  results_final.jsonl  results_final.csv  accuracy.json  review.csv
  cache/
  agent/       schema.py search.py fetch.py mcp_check.py extract.py verify.py review_queue.py run.py
  analysis/    patterns.py accuracy.py
  site/        index.html
  .github/workflows/  research-one.yml  pages.yml
```

---

## 4. Phase 1: Schema (~30 min)

Write `data/apps.csv` from Appendix A (`id,name,category,hint`). Define `agent/schema.py` (pydantic). Every factual field is `{value, evidence_url, evidence_quote, confidence}`:

| Field | Allowed values |
|---|---|
| `category`, `one_liner` | short text |
| `app_type` | `hosted_saas`, `self_hosted_oss`, `cli_tool`, `unclear` |
| `auth_methods` | list: `oauth2`, `api_key`, `basic`, `bearer_token`, `hmac_signature`, `jwt`, `session_cookie`, `none`, `other` (+ note) |
| `oauth_flows` | list: `auth_code`, `client_credentials`, `pkce`, `device`, `n/a` |
| `access_model` | `self_serve_free`, `self_serve_trial`, `paid_plan_required`, `app_review_required`, `admin_approval`, `partner_gated`, `contact_sales`, `not_applicable` |
| `api_type` | list: `rest`, `graphql`, `soap`, `websocket`, `sdk_only`, `cli_only`, `none` |
| `api_breadth` | `narrow`, `medium`, `broad`, `unknown` (+ endpoint count if documented) |
| `openapi_spec` | `yes` (+URL), `no`, `unknown` |
| `webhooks_triggers` | `yes`, `no`, `unknown` |
| `sandbox` | `yes`, `no`, `unknown` |
| `rate_limits` | short text or `unknown` |
| `existing_mcp` | `official`, `community`, `none` (+URL) |
| `already_in_composio` | `yes`, `no`, `unknown` (check Composio's public toolkit catalog at https://docs.composio.dev/toolkits or the dashboard) |
| `buildability` | `green` (buildable today), `yellow` (buildable with a gate or effort), `red` (blocked) |
| `main_blocker` | `app_review`, `paid_plan`, `partner_program`, `contact_sales`, `no_public_api`, `cli_or_local_only`, `self_hosted_per_instance`, `complex_request_signing`, `kyc_or_regional`, `thin_or_unclear_docs`, `enterprise_only`, `waitlist`, `none` |
| `estimated_tool_count` | integer estimate with basis |
| `reasoning` | 1-2 sentences |
| `overall_confidence` | `high`, `medium`, `low` |

Key distinction to capture in `reasoning`/`main_blocker`: (a) can a developer get credentials themselves today vs (b) can Composio ship a managed OAuth app for all users (where app review and partner gates bite, e.g. Google Ads developer token, Meta app review, Amazon SP-API registration).

**Accept:** schema imports; `apps.csv` has 100 rows; a dry-run on one app returns a validated object.

---

## 5. Phase 2: Research agent (~2 hrs)

### Pass 1 (baseline, do not tune)
Per app: one LLM call from model knowledge plus at most one search result page. Run all 100. Save `data/results_pass1.jsonl`. Commit.

### Pass 2 (real pipeline)
Per app, concurrently:
1. **Discover:** 4-6 searches: `"<app> API authentication"`, `"<app> developer getting started"`, `"<app> API pricing access"`, `"<app> OAuth app review"`, `"<app> API rate limits"`, `"<app> MCP server"`. Prefer official domains; use the hint URL as a seed.
2. **Fetch:** top official pages (auth docs, getting-started, pricing/plans, API reference index, OpenAPI link). Cache. JS-heavy or blocked → browser fallback. Record failures.
3. **MCP check:** official MCP registry, GitHub search (`"<app> mcp"`), Smithery, vendor docs. Classify official vs community. Confirm any cited repo really exists and is for this app and is owned by the vendor if called "official".
4. **Extract:** give the LLM ONLY fetched pages; require verbatim quotes; `unknown` when not stated. Validate against schema; retry on validation errors.
5. **Composio catalog check** for `already_in_composio`.

Special handling:
- CLI/OSS tools (Sherlock, Mermaid CLI, Higgsfield CLI): `app_type=cli_tool`; `api_type=cli_only`; judge "wrap as a sandboxed skill" rather than OAuth.
- Self-hosted/per-instance (Twenty, Magento, WooCommerce): `main_blocker=self_hosted_per_instance`; note per-instance base URL.
- Ambiguous names (Pylon, Plain, Gladly, Pumble, fanbasis, Paygent Connect, iPayX, MrScraper, Waterfall.io, Consensus, NotebookLM, Higgsfield): first confirm you identified the right company/product; if not, `low` confidence and send to the human queue.

Save `data/results_pass2.jsonl`. Commit.

---

## 6. Phase 3: Verification loops (~1 hr)

In `agent/verify.py`, produce Pass 3:
1. **Evidence check:** URL returns 200 and the quote (fuzzy match) appears in the cached page. Fail → downgrade the field to `unknown` / unsupported.
2. **Independent verifier:** second model/prompt reads claim + source: `supported | contradicted | not_found`. Contradictions → re-extract with the objection, else the review queue.
3. **Self-consistency:** extract 3x for `auth_methods`, `access_model`, `buildability`, `main_blocker`; majority vote; disagreement → low confidence + review queue.
4. **Rule checks:** `oauth2` without authorize/token URL; `self_serve_free` contradicted by pricing; `green` with a real blocker; `existing_mcp=official` not on the vendor's domain/org; `red` yet `self_serve_free`.
5. **Browser-use spot check** on the ~10 most ambiguous/high-stakes apps: a browser agent independently navigates docs and answers auth + access; compare with the pipeline.
6. **Review queue:** push all flagged/low-confidence rows to a Google Sheet **via Composio** (the middle-path step), also write `data/review.csv` as a backup. Include columns: app, field, agent value, evidence, why flagged, and an empty "human value" column.

Save `data/results_pass3.jsonl`. Commit.

**[HUMAN CHECKPOINT 1]** Tell the human: link to the review sheet/CSV, how many rows flagged, and that they need to fill the "human value" column. Wait. Then apply their corrections (log each in `LOG.md` as agent-wrong/human-right with root cause) → `results_final.jsonl/.csv` (Pass 4).

---

## 7. Phase 4: Accuracy measurement (~1.5 hrs, the most important phase)

1. Build a stratified sample of 30 apps (3 per category) that deliberately includes ~6 obscure apps, ~3 gated/approval-heavy (e.g. Google Ads, Meta Ads, Amazon SP-API, PitchBook), the 3 CLI tools, and a few easy well-documented apps.
2. Split: ~12 **tuning** apps, ~18 **hold-out** apps. Never tune prompts/rules against hold-out.
3. **[HUMAN CHECKPOINT 2]** Generate `data/gold_template.csv` (sampled apps × key fields: auth, access model, api type, existing MCP, buildability, main blocker; with columns for the true value and the source URL). Do NOT pre-fill the agent's answers (avoid anchoring); optionally provide a separate file with agent answers for later comparison. The human labels from the real docs. Wait.
4. `analysis/accuracy.py` compares Pass 1, 2, 3, and 4 (final) with gold: per field and overall, counting correct/partial/wrong/unsupported, with hold-out and tuning reported separately, and sample sizes noted (n is small; say so).
5. List every miss: claim, truth, root cause (stale docs, marketing vs docs contradiction, wrong entity, unreachable page, hallucination) and which loop caught it (if any).
6. Write `data/accuracy.json`. Commit.

Note: tuning happens only between Pass 1 → 2 → 3 using the tuning set. The reported headline accuracy comes from the hold-out set.

---

## 8. Phase 5: Pattern analysis (~45 min)

`analysis/patterns.py` computes from the final data:
- Auth distribution overall and by category (what dominates; where OAuth2 is gated by app review).
- Category × access_model matrix.
- Ranked blocker counts.
- Buildability green/yellow/red overall and per category.
- Existing-MCP coverage (official/community/none) and how many are already in Composio.
- OpenAPI availability vs buildability.
- Segments: **Easy wins** (green + OpenAPI + self-serve), **Needs outreach** (partner-gated, contact-sales, app review), **Not a fit** (CLI-only, no public API).
- `priority_score` (value × ease; document the formula) and a recommended **top-15 build order** with one-line reasons.

Write 3-5 plain-language headline statements using only numbers computed from the data. Save chart data as JSON for the page.

---

## 9. Phase 6: The HTML case study (~1.5 hrs)

Build `site/index.html`: ONE self-contained file (inline CSS/JS, inline SVG or a CDN-pinned chart library; embedded data). Responsive; supports light and dark mode (CSS variables with `prefers-color-scheme`). Order:
1. **Headline:** 3-5 patterns and the verified hold-out accuracy with sample size.
2. **Patterns:** auth chart, category × access matrix, blocker ranking, easy-wins vs outreach lists, recommended build order.
3. **Findings table:** all 100 rows, sortable, filterable (category, auth, access, verdict), verdict and confidence chips, expandable evidence quote + link per row, CSV and JSON download.
4. **Agent:** pipeline diagram (discover → fetch → MCP check → extract → verify → human); what it does; **where a human was needed** (counts from `LOG.md`); the Composio step and what it did.
5. **Proof:** the CLI command (`python -m agent.run --app "Attio"`) and the GitHub Actions `research-one` workflow link with how to trigger it, plus a few example outputs.
6. **Verification:** accuracy-by-pass chart (Pass 1 → 4), per-field table, sample-size caveat, and the full hits-and-misses list with root causes.
7. **Failures and limits:** apps that defeated the agent, unresolved fields, what you'd do at scale, Composio caveats.
8. **Agent-readable:** `<script type="application/json" id="data">` with the full dataset, plus a plain-text summary block near the top.

Design: skimmable in two minutes, plain language, no decoration that hides data.

---

## 10. Phase 7: Deploy and package (~45 min)

1. `.github/workflows/pages.yml` publishing `site/` to GitHub Pages; enable Pages with `gh api`/`gh` or tell the human the one click if the CLI can't.
2. `.github/workflows/research-one.yml` (`workflow_dispatch`, input: app name) that runs the agent for one app and uploads the JSON as an artifact/step summary. Secrets must be set via `gh secret set` (the human confirms once; never echo keys).
3. `README.md` (short): what it is, setup, env vars, how to run one app / all apps / verification, where outputs land, known limits, the live link.
4. Open the live URL and verify: loads, table sorts/filters, downloads work, mobile width OK, dark mode OK. Fix issues.

---

## 11. Final checklist (do not declare done until all true)

- [ ] 100 rows; every claim has evidence URL + quote or is `unknown`
- [ ] Pass 1 baseline accuracy recorded before improvements
- [ ] Hold-out accuracy reported separately from tuning, with n
- [ ] All misses listed on the page with root causes
- [ ] Human interventions listed with counts
- [ ] Headline numbers computed from data (no invented figures)
- [ ] Composio used in at least one real step and described honestly (or the failure described)
- [ ] Public repo with README; no secrets in history (`git log -p | grep -i key` sanity check)
- [ ] Live Pages link works
- [ ] `LOG.md` has a "How it works" section so the human can explain everything in the interview

## 12. Communication style

At each **[HUMAN]** stop: say what you did, what files exist, exactly what you need, and any doubts. Max a few lines. No long summaries.

---

## Appendix A: The 100 apps (`id,name,category,hint`)

```
1,Salesforce,CRM and Sales,salesforce.com
2,HubSpot,CRM and Sales,hubspot.com
3,Pipedrive,CRM and Sales,pipedrive.com
4,Attio,CRM and Sales,attio.com
5,Twenty,CRM and Sales,twenty.com (open-source CRM)
6,Podio,CRM and Sales,podio.com
7,Zoho CRM,CRM and Sales,zoho.com/crm
8,Close,CRM and Sales,close.com
9,Copper,CRM and Sales,copper.com
10,DealCloud,CRM and Sales,api.docs.dealcloud.com
11,Zendesk,Support and Helpdesk,zendesk.com
12,Intercom,Support and Helpdesk,intercom.com
13,Freshdesk,Support and Helpdesk,freshdesk.com
14,Front,Support and Helpdesk,front.com
15,Pylon,Support and Helpdesk,usepylon.com
16,LiveAgent,Support and Helpdesk,liveagent.com
17,Plain,Support and Helpdesk,plain.com
18,Help Scout,Support and Helpdesk,helpscout.com
19,Gorgias,Support and Helpdesk,gorgias.com
20,Gladly,Support and Helpdesk,gladly.com
21,Slack,Communications and Messaging,slack.com
22,Twilio,Communications and Messaging,twilio.com
23,Zoho Cliq,Communications and Messaging,zoho.com/cliq
24,Lark (Larksuite),Communications and Messaging,open.larksuite.com
25,Pumble,Communications and Messaging,pumble.com
26,Discord,Communications and Messaging,discord.com
27,Telegram,Communications and Messaging,core.telegram.org
28,WhatsApp Business,Communications and Messaging,developers.facebook.com/docs/whatsapp
29,Aircall,Communications and Messaging,aircall.io
30,Vonage,Communications and Messaging,developer.vonage.com
31,Google Ads,Marketing/Ads/Email/Social,developers.google.com/google-ads
32,Meta Ads,Marketing/Ads/Email/Social,developers.facebook.com/docs/marketing-apis
33,LinkedIn Ads,Marketing/Ads/Email/Social,learn.microsoft.com/linkedin/marketing
34,GoHighLevel,Marketing/Ads/Email/Social,highlevel.stoplight.io
35,Mailchimp,Marketing/Ads/Email/Social,mailchimp.com/developer
36,Klaviyo,Marketing/Ads/Email/Social,developers.klaviyo.com
37,systeme.io,Marketing/Ads/Email/Social,systeme.io (funnel builder)
38,Pinterest,Marketing/Ads/Email/Social,developers.pinterest.com
39,Threads (Meta),Marketing/Ads/Email/Social,developers.facebook.com/docs/threads
40,SendGrid,Marketing/Ads/Email/Social,sendgrid.com
41,Shopify,Ecommerce,shopify.dev
42,WooCommerce,Ecommerce,woocommerce.com/document/woocommerce-rest-api
43,BigCommerce,Ecommerce,developer.bigcommerce.com
44,Salesforce Commerce Cloud,Ecommerce,developer.salesforce.com/docs/commerce
45,Magento (Adobe Commerce),Ecommerce,developer.adobe.com/commerce
46,Squarespace,Ecommerce,developers.squarespace.com
47,Ecwid,Ecommerce,api-docs.ecwid.com
48,Gumroad,Ecommerce,gumroad.com/api
49,Amazon Selling Partner,Ecommerce,developer-docs.amazon.com/sp-api
50,fanbasis,Ecommerce,fanbasis.com
51,DataForSEO,Data/SEO/Scraping,docs.dataforseo.com
52,SE Ranking,Data/SEO/Scraping,seranking.com/api
53,Ahrefs,Data/SEO/Scraping,ahrefs.com/api
54,MrScraper,Data/SEO/Scraping,docs.mrscraper.com
55,Apify,Data/SEO/Scraping,docs.apify.com
56,Firecrawl,Data/SEO/Scraping,firecrawl.dev
57,Bright Data,Data/SEO/Scraping,brightdata.com
58,Sherlock,Data/SEO/Scraping,github.com/sherlock-project/sherlock
59,Waterfall.io,Data/SEO/Scraping,waterfall.io (contact/company intel)
60,Clay,Data/SEO/Scraping,clay.com
61,GitHub,Developer/Infra/Data,docs.github.com/rest
62,Vercel,Developer/Infra/Data,vercel.com/docs/rest-api
63,Netlify,Developer/Infra/Data,docs.netlify.com/api
64,Cloudflare,Developer/Infra/Data,developers.cloudflare.com/api
65,Supabase,Developer/Infra/Data,supabase.com/docs
66,Neo4j,Developer/Infra/Data,neo4j.com/docs/api
67,Snowflake,Developer/Infra/Data,docs.snowflake.com
68,MongoDB Atlas,Developer/Infra/Data,mongodb.com/docs/atlas/api
69,Datadog,Developer/Infra/Data,docs.datadoghq.com/api
70,Sentry,Developer/Infra/Data,docs.sentry.io/api
71,Notion,Productivity and PM,developers.notion.com
72,Airtable,Productivity and PM,airtable.com/developers
73,Linear,Productivity and PM,developers.linear.app
74,Jira,Productivity and PM,developer.atlassian.com
75,Asana,Productivity and PM,developers.asana.com
76,Monday.com,Productivity and PM,developer.monday.com
77,ClickUp,Productivity and PM,clickup.com/api
78,Coda,Productivity and PM,coda.io/developers
79,Smartsheet,Productivity and PM,smartsheet.com/developers
80,Harvest,Productivity and PM,help.getharvest.com/api-v2
81,Stripe,Finance and Fintech,stripe.com/docs/api
82,Plaid,Finance and Fintech,plaid.com/docs
83,Binance,Finance and Fintech,binance-docs.github.io
84,Paygent Connect,Finance and Fintech,paygent (NMI-powered)
85,iPayX,Finance and Fintech,ipayx.ai/docs
86,QuickBooks,Finance and Fintech,developer.intuit.com
87,Xero,Finance and Fintech,developer.xero.com
88,Brex,Finance and Fintech,developer.brex.com
89,Ramp,Finance and Fintech,docs.ramp.com
90,PitchBook,Finance and Fintech,pitchbook.com (research API)
91,NotebookLM,AI/Research/Media-native,cloud.google.com/gemini (Enterprise API)
92,Otter AI,AI/Research/Media-native,help.otter.ai (MCP server)
93,Fathom,AI/Research/Media-native,fathom.video
94,Consensus,AI/Research/Media-native,consensus.app (OAuth requested)
95,Reducto,AI/Research/Media-native,reducto.ai (document parsing)
96,Devin,AI/Research/Media-native,docs.devin.ai (MCP)
97,higgsfield,AI/Research/Media-native,higgsfield.ai/cli (content suite)
98,Mermaid CLI,AI/Research/Media-native,github.com/mermaid-js/mermaid-cli
99,YouTube Transcript,AI/Research/Media-native,transcriptapi.com
100,Grain,AI/Research/Media-native,grain.com (meeting notes)
```
