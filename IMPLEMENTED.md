# Upsell Machine — what's built

Project 5: Customer Upsell, Retention & Decision-Making Automation.
Built for the SSC Hackathon theme *Agentic, API-First: Reimagine a Core Workflow*.
Last updated: 11 August 2026.

---

## The app in one paragraph

**Gaia ARR Growth Agent** watches a SecurityScorecard portfolio and tells a CSM which
accounts to act on and what to say. The screen is a single **Opportunities** board:
every signal we can detect, in four lanes, each card carrying a drafted email with the
recipient already resolved. Behind it, two things run without being asked — a **daily
research agent** that searches the news for every account and extracts structured
events, and an **MCP server** that exposes the same portfolio tools to any MCP client,
so a CSM can work the portfolio from Claude Desktop with no interface of ours involved.
Everything is built on SSC APIs; none of it uses an existing SSC frontend.

### Where the agent actually is

The brief warns against building another dashboard. Worth being precise about how far
we escape that, because the honest answer is "partly".

**The board itself is not agentic.** It's deterministic rules over live SSC data. Good
engineering, but a rules engine — the CSM still scans and prioritises.

**Two things behind it are.** The daily research agent picks queries per account, pulls
Google News, and decides which stories are real acquisitions, expansions or launches
before extracting them — unattended, on a schedule, with an LLM making the judgement
calls. And the MCP server hands a tool-calling agent the same four tools, letting it
choose which accounts to examine rather than following a fixed query.

**What isn't reachable from the current UI.** A `Today` briefing endpoint (three ranked
actions with drafted emails) and an `Ask` conversational agent are both built, tested
and live at `/today` and `/agent/chat` — but the UI was consolidated to the single board
and no longer links to them. They remain available over the API and through MCP. This is
a deliberate team decision to keep one clean surface, not an abandoned feature.

---

## The entry points

| Entry point | What it is | Status |
|---|---|---|
| **Opportunities board** | Every signal, four lanes, drafted email per card | **The UI.** What you see on screen |
| **Daily research agent** | Searches news per account, extracts structured events, unattended | **Running.** Surfaced as "Auto-researched <date> · Run now" |
| **MCP server** | The same portfolio tools over Model Context Protocol | **Working.** The agentic demo — see [MCP.md](MCP.md) |
| **`/today`, `/agent/chat`** | Ranked worklist; conversational agent | **Built, API-only.** No UI path in the current design |

All of them share one tool layer (`app/services/agent_tools.py`), so they cannot drift
apart.

---

## Data provenance — important for demos

The UI labels this everywhere, but to be explicit here too: every row below names the
exact call, file and cache lifetime behind it. Hover the <abbr title="In the app this is a click-to-reveal button (InfoPopover.tsx), not hover — markdown can't run React. Same ⓘ glyph, same intent: show the source without leaving the page.">ⓘ</abbr>
for the microdetail; where the vendor publishes real docs, the field name itself links
out to them.

| Data | Exact source | Status |
|---|---|---|
| [SSC current score, grade, industry](https://securityscorecard.readme.io/reference) <abbr title="GET /companies/{domain}. In-process response cache, 10 minutes (_CACHE_TTL_SECONDS = 600). backend/app/services/ssc_client.py, get_company(), line 106-108.">ⓘ</abbr> | SecurityScorecard API | **Live** |
| [SSC score history](https://securityscorecard.readme.io/reference) <abbr title="GET /companies/{domain}/history/score, timing=weekly, from = today − 190 days. Feeds the 30-day and 182-day delta thresholds (±5 pts / ±10 pts) and the >95 flag. backend/app/services/ssc_client.py, get_score_history() + build_score_summary(), line 127-209.">ⓘ</abbr> | SecurityScorecard API | **Live** |
| [Third-party / supplier detection](https://securityscorecard.readme.io/reference) <abbr title="GET /vendor-detection/{domain}/third-party, limit=50. No portfolio membership required — a fully read-only lookup. Filtered against a denylist of infrastructure/OSS false-positives (Apache, nginx, OpenSSL, CNCF, ...). backend/app/services/ssc_client.py, get_third_party_vendors(), line 111-124; filter in opportunities.py, _NOT_REAL_VENDORS.">ⓘ</abbr> | SecurityScorecard API | **Live** |
| Portfolio membership (roster sync) <abbr title="GET/POST /portfolios to find-or-create one shared, org-visible portfolio named 'Upsell Machine Dashboard - Demo Domains - Do Not Delete'; PUT .../companies/{domain} to add a tracked domain; GET .../companies to read it back for 'Sync from portfolio'. backend/app/services/ssc_client.py, line 50-104.">ⓘ</abbr> | SecurityScorecard API | **Live** |
| Customer roster (names, domains) <abbr title="Seed list at backend/data/customers.json, extended by the 'Add customer' form or by 'Sync from portfolio', which reads back anything added directly in the SSC UI. backend/app/storage.py, load_customers()/create_customer().">ⓘ</abbr> | `backend/data/customers.json` + SSC portfolio sync | **Live** roster, mixed-provenance rows |
| News events (acquisitions, offices, launches) <abbr title="Feed: https://news.google.com/rss/search?q=... — headline, publish date, publisher and article link only, no article body (the DuckDuckGo/cloudscraper body-scraper was removed, see Known limitations). Extraction: OpenAI gpt-4o-mini, response_format=json_object, same prompt rules as the manual flow. Cached per domain at backend/data/news_events/{domain}.json. backend/app/services/web_research.py.">ⓘ</abbr> | [Google News RSS](https://news.google.com/rss/search?q=example) → [OpenAI](https://platform.openai.com/docs/api-reference/chat) extraction | **Researched**, cached, with a link to the source article |
| Decision-makers / job titles <abbr title="No API call from our backend. decision_maker_prompt.py builds a prompt (employment test, fit test, title-evidence hierarchy, CISO/BISO priority, LinkedIn URL verification); a human runs it in Claude, which reaches indexed LinkedIn snippets our server can't fetch (a direct server-side fetch of a public LinkedIn profile returns 0 characters — login wall). Pasted-back JSON is parsed and cached at backend/data/decision_makers/{domain}.json. backend/app/routers/decision_makers.py (import endpoint).">ⓘ</abbr> | Research prompt run in [Claude](https://claude.ai/), pasted back | **Researched**, cached |
| Agent reasoning (Today, Ask) <abbr title="gpt-4o-mini by default, overridable via AGENT_MODEL. Tool-calling loop over the same four tools MCP exposes (agent_tools.py); every tool call and its token cost is surfaced in the response. backend/app/services/agent.py, line 66-141.">ⓘ</abbr> | Live tool calls over the above | **Live** |
| Platform usage (logins, slots, reports) <abbr title="Python's random.Random, seeded on customer_id for the licensed-slot cap (a contract property) and on f'{customer_id}:{today}' for everything else — deterministic per customer per day, so demos are stable within a day but drift day to day. No real feed exists yet. backend/app/services/mock_usage.py.">ⓘ</abbr> | [Deterministic placeholder generator](https://docs.python.org/3/library/random.html#random.Random) | **Sample** — marked `◇ Sample data` |
| Sponsor / CSM assignment <abbr title="sponsor and csm fields in backend/data/customers.json, hand-entered — no CRM/Salesforce connection exists. See 'Why we're blocked on the rest' for what would replace this.">ⓘ</abbr> | Seed data | **Sample** — no CRM connected |

### Four tiers, always labelled

Every card carries an icon for its tier — no card is unmarked.

| Tier | Meaning | Count | How it looks |
|---|---|---|---|
| **Live** | Read directly from the SecurityScorecard API | 9 | Green live icon |
| **Researched** | Real, but assembled by us from public sources and cached | 23 | Petrol researched icon |
| **Sample** | Real trigger logic, placeholder *input* data | 6 | Grey sample icon |
| **Concept** | Trigger not built — an illustration of what it would surface | 13 (off by default) | `⚑ Not built — concept`, plus the trigger number and the data source it's waiting on |

Two distinctions worth drawing. **Live vs researched:** a score comes back from an API
and is as true as SSC's data; a news event was searched for and extracted by a model, so
it carries more uncertainty and is worth flagging as such. **Sample vs concept:** sample
cards run production logic on placeholder numbers, concept cards are pure illustration
with invented numbers and no logic behind them.

**Concept cards are off by default** — the honest view is the one you get without
thinking about it. Tick *"Show unbuilt triggers as concepts"* in the board legend to
reveal them, which turns the board into the full 23-trigger product vision. They're
distributed one per account rather than stamped on every customer, so the board stays
legible and looks like a realistic spread of activity.

The board legend carries an icon per tier, each with a click-through explaining what
that source is.

---

## Trigger coverage: 13 built, all 23 represented

Against the ranked trigger list in *"Automate customer engagement opportunities to
drive ARR growth"*.

### Built

| # | Trigger | Data source |
|---|---|---|
| 1 | Nearing full utilisation of licensed vendor slots | Sample usage <abbr title="slots_used / licensed_slots >= 0.85 (_SLOT_CAPACITY_WARN_PCT). Both numbers come from mock_usage.py's per-customer/per-day generator. signals.py, build_signal().">ⓘ</abbr> |
| 2 | Acquisition announced | Automated news research <abbr title="gpt-4o-mini classifies each headline's event_type; 'acquisition' events become this card. Deduplicated across outlets by shared named subject (opportunities.py, _dedupe_news_events()).">ⓘ</abbr> |
| 3 | Increasing utilisation of portfolio slots | Sample usage <abbr title="slots_delta_7d, the difference between this week's and last week's slots_filled_7d in mock_usage.py. Computed by the signal layer and served over /signals; no standalone card — folds into the Usage lane's slot-capacity signal.">ⓘ</abbr> |
| 5 | New offices / regional operations | Automated news research <abbr title="event_type == 'expansion' from the same Google News → gpt-4o-mini pipeline as trigger #2.">ⓘ</abbr> |
| 6 | New product or service launch | Automated news research <abbr title="event_type == 'launch' from the same Google News → gpt-4o-mini pipeline as trigger #2.">ⓘ</abbr> |
| 7 | Supplier breach anticipated | **Live** <abbr title="Worst-scoring entry from GET /vendor-detection/{domain}/third-party below _SUPPLIER_RISK_SCORE_THRESHOLD = 50, after the infrastructure/OSS denylist. opportunities.py.">ⓘ</abbr> — SSC vendor-detection scores |
| 10 | High platform engagement | Sample usage <abbr title="engagement_score = slots_filled_7d*3 + reports_generated_7d + total_visits_7d, threshold 75 (_ENGAGEMENT_THRESHOLD). All three inputs are mock_usage.py numbers. signals.py, build_signal().">ⓘ</abbr> |
| 11 | Close peer breach anticipated | **Live** <abbr title="Largest SSC score decline among other tracked customers sharing the same industry field — the peer is never named, only the industry and the delta. opportunities.py, 'close peer breach anticipated', line ~399-417.">ⓘ</abbr> — SSC scores, anonymised across tracked customers |
| 12 | Top security score within industry | **Live** <abbr title="Customer's current score is the max among all tracked customers sharing its SSC industry field. opportunities.py + signals.py industry_top_ids()/industry_stats().">ⓘ</abbr> — SSC scores |
| 13 | Significant SSC score increase | **Live** <abbr title="delta_30d > 5 or delta_182d > 10, computed against GET /companies/{domain}/history/score. ssc_client.py, build_score_summary().">ⓘ</abbr> — SSC score history |
| 17 | New stakeholders identified (DMU) | Decision-maker research <abbr title="A person present in the latest pasted-back decision-maker JSON who wasn't in the previous cached list for that domain — status='new'. opportunities.py, decision-maker diff block.">ⓘ</abbr> |
| 19 | Alumni joins another customer org | Cross-customer decision-maker diffing <abbr title="Matches a newly-identified person's name (or LinkedIn URL) against every other tracked customer's cached decision-maker list — no LinkedIn Sales Navigator involved, just our own accumulated research. opportunities.py, line ~486-500.">ⓘ</abbr> |
| 21 | New user logs in for the first time | Sample usage <abbr title="A name in this day's mock_usage.py individuals list that isn't in backend/data/usage_individuals/{customer_id}.json yet; that file is then updated. mock_usage.py, build_usage_summary().">ⓘ</abbr> |

Trigger #3 is computed by the signal layer and served over `/signals`, but has no card
of its own on the board — it shows up as part of the Usage lane's slot-capacity signal.

### Not built — blocked on data or access

Each of these has a **concept card** in the UI (toggle them on in the board legend)
showing what it would surface once the data source exists.

| # | Trigger | What it needs |
|---|---|---|
| 4 | New regulation impacts industry | Regulatory tracking feed; high false-positive risk |
| 8 | SSC successfully anticipates a breach | Breach event feed + retrospective join |
| 9 | Measurable cost savings | An agreed ROI / avoided-incident model |
| 14 | Reduction in high-risk suppliers | Per-customer supplier portfolios in SSC |
| 15 | Supplier portfolio average score increase | Same as #14 |
| 16 | Share price up vs peers | Stock market data API |
| 18 | Customer compliment in Customer Forum | Access to whichever forum tool this is |
| 20 | A DMU posts about cybersecurity | Social listening; LinkedIn API is partner-gated |
| 22 | A non-DMU user posts about cybersecurity | Same as #20 — but a distinct play: spotting a potential champion, not replying to a known contact |
| 23 | Upcoming CSM meeting identified | Salesforce / calendar integration |

---

## Features

**Opportunities board** (the whole UI)
- Greets the current CSM by name; the same name signs every drafted email
- Four lanes: **Own Cyber Posture**, **Usage**, **Suppliers**, **News**
- Searchable multi-select customer picker with logos, filtering the board
- Default / Detailed / Compact view modes plus a text-size control
- Short active-voice copy on each card, with the fuller explanation on click
- Provenance icons with click-through info, and the concept-card toggle
- Daily research status + "Run now"
- Static link out to the SecurityScorecard portfolio

**Email drawer** (click any card)
- **Editable** subject and body, **recipient dropdown** (any tracked decision-maker or
  the sponsor), reset-to-default, copy to clipboard, mark-as-actioned (session-only)
- For news cards, a link to the source article — shown in the drawer and appended to
  the drafted email, so a CSM congratulating someone has the story attached

**MCP server** — the same tools over Model Context Protocol, so any MCP client can
drive the workflow with no frontend of ours. See [MCP.md](MCP.md).

**Built, but not surfaced in the current UI**
- `/today` — agent surveys every account, drills into what matters, returns 3 ranked
  actions with drafted emails. Cached per calendar day
- `/agent/chat` — conversational agent over live portfolio data, reporting which tools
  it chose and the tokens each answer cost
- `/customers/*` — per-account detail, manual add, and **Sync from portfolio** to
  import anything added directly in the SecurityScorecard UI

**Research**
- *Automated*: news research runs daily across all customers, and on demand per
  customer. Google News RSS → OpenAI extracts structured JSON.
- *Manual*: generates a copy/paste prompt you run in Claude, then paste the JSON back.
  This is the better path for decision-makers — public search rarely names a company's
  security leadership, and the prompt refuses to invent people.

---

## Running it

Backend:
```bash
cd backend && .venv/Scripts/python -m uvicorn app.main:app --reload --port 8000
```
Frontend:
```bash
cd frontend && npm run dev
```
Open http://localhost:5173.

`backend/.env` needs:
- `API_KEY` — SecurityScorecard. Required.
- `OPENAI_API_KEY` — optional. Only powers automated research; without it those
  buttons disable and the copy/paste flow still works.

### Demo safety net

Live research is non-deterministic and rate-limited, so a demo shouldn't depend on it
succeeding on the day. `backend/demo.py` snapshots a known-good data state and restores
it in seconds:

```bash
cd backend
.venv/Scripts/python demo.py snapshot   # capture the current state as the baseline
.venv/Scripts/python demo.py status     # compare live state vs baseline
.venv/Scripts/python demo.py restore    # put the baseline back, then restart the backend
```

`restore --fresh` restores the customer roster but clears the research caches — use it
to demo research populating from empty. Only touches `backend/data/`; never credentials.

### Suggested walkthrough (3–5 minutes)

Open on the board. Land the autonomy claim early, then finish in Claude Desktop.

1. **The board** — *"38 open opportunities across 13 accounts, and every one of them
   came from a live API call."* Walk the four lanes in a sentence each.
2. **Open a News card.** The drafted email is already addressed to the right person,
   with the article attached. *"The CSM edits or sends. They don't write from scratch."*
3. **Point at "Auto-researched <date> · Run now".** This is the strongest autonomy
   line, and it's verifiable: *"that ran by itself this morning, across all 13 accounts,
   and added 5 events. Nobody triggered it."*
4. **Say the privacy line** — *"when a model is involved, it never sees a customer name.
   It sees CUST_A with a score. We tested that no identifier leaks, including inside
   free text."*
5. **Tick "Show unbuilt triggers as concepts"** — the full 23-trigger vision, each card
   naming the data source it's waiting on. Turns "what's missing" into a shopping list.
   **This is the moment that separates you from a team that faked it.**
6. **Finish in Claude Desktop over MCP.** Ask *"which accounts have supplier risk I
   should know about?"* and let the tool calls show. *"Same data, same tools, no UI of
   ours involved — the agent decides what to look at."*

**If asked "what's actually agentic here?"** — be straight: the board is rules, and the
rules are honest. The agency is in two places. The daily research agent decides which
stories are real events worth surfacing, unattended. And over MCP, the agent chooses
which accounts to examine — it surveys 13 cheaply, then drills into two or three.
Nobody wrote that rule; it decides per question, and you can watch it decide.

---

## Data protection: identities never reach the model

The hackathon rules say *"do not send sensitive customer data to third parties."* We
took that seriously enough to design around it rather than hope nobody asked.

**The insight:** a score alone isn't sensitive — "some company scored 91" tells you
nothing. A company name alone isn't especially sensitive either. What's sensitive is
the two **joined together**: *"Stripe is at risk."*

So we break the link, not the data:

| Field | Sent to the model as | Why |
|---|---|---|
| Customer name, domain | `CUST_A` | The sensitive half |
| Person names | `PERSON_1` (role kept) | Personal data; the role is what a CSM needs |
| Score, grade, deltas, dates | **Unchanged** | The agent must rank and compare these |

Real names are restored before anything reaches the screen. The agent reasons exactly
as well, because thresholds and rankings don't care what something is called.

**Verified, not assumed.** We captured the actual outbound payload — 9,242 characters —
and asserted that none of the 28 known customer names, domains or person names appear
anywhere in it, including inside free-text fields like signal reasons and news
headlines. That test caught a real leak path: `"New decision-maker identified: Marco
Silva"` now reads `"...identified: PERSON_2 (Head of Third Party Risk)"` — name gone,
role intact.

**Two honest limits:**
- This is pseudonymisation, not anonymisation. Under GDPR the result is still personal
  data, and in a 13-customer portfolio context can re-identify.
- **Research can't be masked** — you can't search the news for "CUST_A", the real name
  *is* the query. But that path sends only a company name and public web content, with
  no scores or signals attached. Roughly what a search engine already sees.

We also removed the DuckDuckGo scraper: it relied on `cloudscraper`, which exists to
defeat bot detection, and it had stopped working under rate limiting. Google News RSS
is a legitimate feed and turned out to be sufficient alone.

---

## The core principle: every gap is a connection, not a rebuild

**Where a real API exists, the feature is already automated. Where one doesn't, the
same logic runs manually through a prompt — and swapping in the API later is a
configuration change, not a rewrite.**

This is deliberate architecture, and it's the main thing to take away:

| Capability | Today | When connected to an API |
|---|---|---|
| SSC scores, suppliers | **Automated** — live API | Already done |
| News / M&A / launches | **Automated** — runs daily, unattended | Already done |
| Decision-makers | Manual prompt → paste JSON | Same prompt, same parser, same cache — automated |
| Platform usage | Placeholder generator | Replace one module; every trigger it feeds goes live |
| Sponsor / CSM | Seed data | Salesforce sync replaces the roster source |

Both research paths already share the *same* prompt rules, the *same* JSON schema, and
the *same* storage and diffing code. The manual flow isn't a stopgap built to be thrown
away — it's the identical pipeline with a human doing the retrieval step. That's why
news went from manual to fully automated with no change to the prompt or the parser.

---

## Known limitations

Stated plainly, because they matter for judging what's demo-ready vs production-ready.

**Data**
- **Platform usage is placeholder data.** This is the single biggest gap — four
  triggers (1, 3, 10, 21) depend on it. Numbers are deterministic per customer per day
  so demos are stable, and everything derived from it is tagged `◇ Sample data` in the
  UI. It is *shaped* like a real feed, so swapping in real data is a module swap.
- **Sponsor / CSM assignments are seed data.** No CRM is connected.
- **10 of 23 triggers aren't built**, all blocked on data we don't have access to
  (breach feeds, supplier portfolios, share price, forum/social, CRM) — not on
  engineering effort.

**Research**
- **Decision-maker auto-research returns almost nobody** — retrieval limitation, not a
  prompt or model problem. Detailed below.
- **News research is headline-only.** We removed the article-body scraper (it relied on
  an anti-bot bypass and had stopped working), so extraction works from Google News
  headlines, dates and publishers rather than full text.
- **Article links are Google News redirects.** The feed never exposes the publisher's
  own URL, so the link is a long `news.google.com` redirect. It resolves correctly in a
  browser, but reads like a tracking link if a CSM forwards it untouched.
- **Some news is adjacent rather than about the customer.** A headline like "Synchrony
  expands CareCredit through a partnership with Stripe" is filed under Stripe. Still a
  usable hook, but it's the partner's news.

**Interface**
- **The agent has no UI.** `/today` and `/agent/chat` are built and working but the
  consolidated board doesn't link to them, so the tool-calling agent is only reachable
  over MCP or the API. Deliberate, but it means a judge looking only at the screen sees
  automation rather than agency.
- **Company logos don't load.** The board requests them from `logo.clearbit.com`, which
  doesn't resolve in our environment; every card falls back to an initials avatar, and
  the failed requests show as console errors. Cosmetic, and left as-is by team decision.
- **Research quality is only as good as public reporting.** Small or private companies
  produce thin results.

**Engineering**
- **The scheduler runs in-process** — it only fires while the backend is up, and state
  is a JSON file. Fine at this scale; production wants cron or a task queue.
- **Storage is JSON files, not a database.** No concurrent-write safety. Correct call
  for a hackathon, wrong one for multiple CSMs using it at once.
- **No authentication.** Anyone who can reach the port can use it.
- **"Mark as actioned" is session-only**, cleared on reload — there's no per-user
  identity to attribute it to yet.
- **No automated tests.** Verification has been manual against live data.
- **Single-tenant, local-only.** Not deployed anywhere.

---

## Why decision-maker research stays manual

The research prompt is good — it works well when a person runs it in Claude. The
difference is the *retrieval layer*, not the prompt or the model. Measured, not assumed:

| Source | Server-side result |
|---|---|
| Fetching a public LinkedIn profile | **0 characters** — login wall / bot check |
| DuckDuckGo scrape | **0 results** — rate-limited after modest use |
| Google News RSS | Works, but reports what a company *does*, not who its CISO *is* |

Run in Claude, the same prompt gets indexed LinkedIn snippets and can search
iteratively — refining queries based on what it finds. Our pipeline does one
search → scrape → extract pass over whatever it managed to fetch. When the model
returned nobody, it was correct: no evidence, and the prompt forbids guessing.

Fixing this needs a real search API, not better prompting. Free tiers as of Aug 2026:

| Provider | Free tier | Verdict |
|---|---|---|
| Tavily | 1,000 credits/mo, recurring | Best option; ~at our usage ceiling |
| Exa | 1,000 requests/mo, recurring | Comparable |
| Serper | 2,500 one-time trial | Expires, then paid |
| Google CSE | 100/day, but closed to new signups, EOL 1 Jan 2027 | Not viable |
| Brave | Free tier removed Feb 2026 | Not viable |

At ~13 customers × 3 queries daily we'd use ~1,170 queries/month — at the ceiling of the
recurring free tiers with no headroom for growth or on-demand runs, on throttled
no-SLA plans. Given people change roles only a few times a year, manual research is
both cheaper and better here. Revisit if the roster grows or the budget appears.

---

## Why we're blocked on the rest — for the team

Every unbuilt trigger is blocked on **access to data**, not on engineering time. Worth
being precise about which, because they're not all the same kind of blocked.

**1. No access to the data source** — the biggest group.
Platform usage (logins, slots, reports) has no API we can reach, so triggers 1, 3, 10
and 21 run on placeholder numbers. Per-customer supplier portfolios aren't configured
in SSC, blocking 14 and 15. There's no breach-event feed for 8. Share price (16) needs
a paid market-data API. Customer Forum (18) is a tool we have no access to.
*These are procurement or configuration questions, not coding ones.*

**2. Blocked on an organisational answer.**
Trigger 23 needs Salesforce. We don't currently know whether Cyber Rescue uses
Salesforce at all — worth confirming before anyone builds against it. The same
integration would replace our placeholder sponsor/CSM data.

**3. Blocked on a technical limit we measured.**
Automated decision-maker research (17) returns almost nobody, and we proved why rather
than guessing: fetching a public LinkedIn profile server-side returns **0 characters**
(login wall), and DuckDuckGo rate-limits after modest use. Meanwhile news headlines
don't name a company's CISO. The same prompt works when a person runs it in Claude,
because Claude's web search reaches indexed LinkedIn snippets that no server-side
scrape can. **This is a retrieval limitation, not a prompt or model problem** — which
is why that one path stays manual and is genuinely better for it.

**4. Not a blocker, an unknown.**
The brief names the **Titan API** as the primary target and PV1 as a fallback. We built
entirely on PV1 (`api.securityscorecard.io`) because we have no Titan documentation or
access. If Titan covers scores, score history and vendor detection, swapping is
contained work — every SSC call already routes through one module, `ssc_client.py`.
**Worth asking at kick-off.**

### What this means for the pitch

The honest framing is that we're **not blocked on ideas or implementation**. Each gap
has a working card in the UI showing exactly what it would surface, and names the data
source it's waiting for. That turns "what's missing" into a shopping list rather than
an apology.

---

## Does it fit the judging criteria?

An honest self-assessment, including where we're weak.

| Criterion | Where we stand | Read |
|---|---|---|
| **Fits theme** — genuinely agentic and API-first? | **Agentic:** a daily research agent that runs unattended and decides what counts as a real event, plus a tool-calling agent over MCP that chooses which accounts to examine. **API-first:** everything from SSC APIs, and via MCP no frontend at all. *Weak spots: we're on PV1 not Titan, and the on-screen board is rules rather than agency* | Good, not Strong |
| **Practicality** | Real CSM problem from the actual project brief, live SSC data, honest labelling of what's placeholder | Strong |
| **Business potential** | Directly ARR-linked. Deployment config, auth and a documented POC→production path already exist | Strong |
| **Token efficiency** | ~4.4k tokens per Ask query, ~5.2k for a daily briefing, on a low-cost model. Tools return the smallest useful shape so the agent surveys cheaply and drills selectively. Token count is visible in the UI | **Probably our strongest, and most teams will ignore this criterion** |
| **Wow factor** | Live data end to end, unattended daily research, editable drafted emails with the source article attached, honest provenance, and the concept toggle revealing the full 23-trigger vision | Good |

**Where we're genuinely weak:**
- **Not using Titan**, which the brief calls the primary target.
- **Platform usage is placeholder**, and four triggers depend on it.
- **10 of 23 triggers unbuilt** — all data-blocked, but still unbuilt.
- **The agent isn't visible on screen.** Our strongest agentic assets — the tool-calling
  loop and the ranked worklist — need MCP or the API to reach. A judge who only watches
  the demo screen won't see them unless we show them.
- **No automated tests.** Verification has been manual against live data.

**The strongest single claim we can make:** the agent decides which accounts to
examine, does it in ~5k tokens on a cheap model, and never sends a customer's identity
joined to their security posture to a third party — and we tested that rather than
assuming it.

---

## What would move this furthest, fastest

1. **A real platform-usage feed.** Biggest sample-data surface — would make triggers
   1, 3, 10, 21 genuinely live.
2. **Salesforce access.** Unblocks #23 and replaces sample sponsor/CSM data.
3. **Per-customer supplier portfolios in SSC.** Unblocks #14 and #15.
4. **An agreed ROI model.** Unblocks #9, which is the strongest renewal-conversation
   asset in the whole list.
