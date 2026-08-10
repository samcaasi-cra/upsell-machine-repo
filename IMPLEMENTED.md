# Upsell Machine — what's built

Project 5: Customer Upsell, Retention & Decision-Making Automation.
Built for the SSC Hackathon theme *Agentic, API-First: Reimagine a Core Workflow*.
Last updated: 10 August 2026.

---

## The app in one paragraph

An **agent** that reviews a SecurityScorecard portfolio and tells a CSM what to do
today. It reaches them three ways: **Today** hands back three ranked actions with the
outreach already drafted; **Ask** answers questions about the portfolio in plain
English; and an **MCP server** exposes the same tools to any MCP client, so a CSM can
work from Claude Desktop with no interface of ours involved. Two supporting views
remain for inspection and override — an **Opportunities** board of every signal, and a
**Customers** drill-down per account. Everything is built on SSC APIs; none of it uses
an existing SSC frontend.

### Why it isn't a dashboard

The brief warns against building another dashboard, and it's right to. A board of 38
signals across 13 accounts makes the CSM the reasoning engine — they scan, filter,
prioritise and decide.

**Today** inverts that. The agent surveys every account, drills into the ones that
matter, and returns three things to do in order, each with the email written. The CSM
approves or skips. The board still exists, because someone will always want to see
everything — but it's the fallback, not the front door.

---

## The three entry points

| Entry point | What it is | Why it exists |
|---|---|---|
| **Today** | Agent-produced worklist: 3 ranked actions, reasons, drafted emails. Cached daily | The default. A decision, not a data dump |
| **Ask** | Conversational agent over live data, showing which tools it chose and tokens used | Ad-hoc questions a fixed view can't anticipate |
| **MCP server** | The same tools over Model Context Protocol | Works with no frontend at all — see [MCP.md](MCP.md) |

All three share one tool layer (`app/services/agent_tools.py`), so they cannot drift
apart.

---

## Data provenance — important for demos

The UI labels this everywhere, but to be explicit:

| Data | Source | Status |
|---|---|---|
| SSC scores, grades, industry, score history | SecurityScorecard API | **Live** |
| Third-party supplier detection + their scores | SecurityScorecard API | **Live** |
| Customer roster | `backend/data/customers.json` + SSC portfolio sync | **Live** |
| News events (acquisitions, offices, launches) | Google News RSS → OpenAI extraction | **Live, cached** |
| Decision-makers / job titles | Research prompt run in Claude, pasted back | **Live, cached** |
| Agent reasoning (Today, Ask) | Live tool calls over the above | **Live** |
| Platform usage (logins, slots, reports) | Deterministic placeholder generator | **Sample** — marked `◇ Sample data` |
| Sponsor / CSM assignment | Seed data | **Sample** — no CRM connected |

### Three tiers, always labelled

| Tier | Meaning | How it looks |
|---|---|---|
| **Live** | Real data from a real source | Normal card |
| **Sample** | Real trigger logic, placeholder *input* data | `◇ Sample data` tag |
| **Concept** | Trigger not built — an illustration of what it would surface | Dashed striped card, `⚑ Not built — concept`, plus the trigger number and the data source it's waiting on |

The distinction between *sample* and *concept* matters: sample cards run production
logic on placeholder numbers, concept cards are pure illustration with invented numbers
and no logic behind them.

**Concept cards are off by default** — the honest view is the one you get without
thinking about it. Tick *"Show unbuilt triggers as concepts"* in the board legend to
reveal them, which turns the board into the full 23-trigger product vision. They're
distributed one per account rather than stamped on every customer, so the board stays
legible and looks like a realistic spread of activity.

The Opportunities board carries a provenance legend; the Customers table marks each
column `● live SSC` / `◆ researched` / `◇ sample`.

---

## Trigger coverage: 14 of 23

Against the ranked trigger list in *"Automate customer engagement opportunities to
drive ARR growth"*.

### Built

| # | Trigger | Data source |
|---|---|---|
| 1 | Nearing full utilisation of licensed vendor slots | Sample usage |
| 2 | Acquisition announced | Automated news research |
| 3 | Increasing utilisation of portfolio slots | Sample usage |
| 5 | New offices / regional operations | Automated news research |
| 6 | New product or service launch | Automated news research |
| 7 | Supplier breach anticipated | **Live** — SSC vendor-detection scores |
| 10 | High platform engagement | Sample usage |
| 11 | Close peer breach anticipated | **Live** — SSC scores, anonymised across tracked customers |
| 12 | Top security score within industry | **Live** — SSC scores |
| 13 | Significant SSC score increase | **Live** — SSC score history |
| 17 | New stakeholders identified (DMU) | Decision-maker research |
| 19 | Alumni joins another customer org | Cross-customer decision-maker diffing |
| 21 | New user logs in for the first time | Sample usage |

Trigger #3 currently surfaces on the Customers table only, not as a board card.

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
| 22 | A non-DMU user posts about cybersecurity | Same as #20 |
| 23 | Upcoming CSM meeting identified | Salesforce / calendar integration |

---

## Features

**Today** (landing screen)
- Agent surveys every account, drills into what matters, returns 3 ranked actions
- Each carries the reason, the concrete next step, and a drafted email
- Cached per calendar day; "Refresh" forces a rebuild
- Shows token cost and that identities were masked

**Ask** (conversational agent)
- Natural-language questions over live portfolio data
- Displays which tools the agent chose to call, and the tokens each answer cost
- Suggested questions to start from

**MCP server** — the same tools over Model Context Protocol, so any MCP client can
drive the workflow with no frontend of ours. See [MCP.md](MCP.md).

**Opportunities board**
- Four lanes: Proof of Value, Adoption Signals, Expansion Events, Engagement Prompts
- Account chips with live SSC grade + score, filter the board by account
- Per-card drafted email with resolved recipient
- Email drawer: **editable** subject and body, **recipient dropdown** (any tracked
  decision-maker or the sponsor), reset-to-default, copy to clipboard,
  mark-as-actioned (session-only)
- Daily research status + "Run now"

**Customers tab**
- Risk-sorted table with signal badges and per-column provenance labels
- Detail view: SSC score chart, usage breakdown, decision-maker table with LinkedIn
  links, news table
- Add customer manually, or **Sync from portfolio** to import anything added directly
  in the SecurityScorecard UI

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

Lead with the agent. The board is supporting evidence, not the story.

1. **Today** — open on it. *"The agent reviewed all 13 accounts and picked 3 worth your
   time."* Read the top one aloud: the reason cites real numbers. Expand the draft
   email. Point at the footer — **N tool calls, ~5k tokens, once a day**.
2. **Ask** — type *"who has supplier risk I should know about?"*. Point at the tool
   chips as they appear: **it chose `list_customers`, then drilled into two accounts.**
   That's the agent deciding, not a fixed query.
3. **Say the privacy line** — *"the model never saw a customer name. It saw CUST_A with
   a score. We tested that no identifier leaks, including inside free text."*
4. **Opportunities** — *"and if you want everything, it's here"* — legend, lanes, a
   `◇ Sample data` card called out honestly.
5. **Tick "Show unbuilt triggers as concepts"** — the full 23-trigger vision, each card
   naming the data source it's waiting on. Turns "what's missing" into a shopping list.
6. **Close on architecture**: every gap is a connection, not a rebuild — news already
   made exactly that transition from manual to automated with no prompt or parser
   change. And mention **MCP**: the same tools work with no frontend at all.

**If asked "what's actually agentic here?"** — the agent chooses which accounts to
examine. It surveys 13 cheaply, then fetches detail on 3. Nobody wrote that rule; it
decides per question, and you can watch it decide in the Ask tab.

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
- **9 of 23 triggers aren't built**, all blocked on data we don't have access to
  (breach feeds, supplier portfolios, share price, forum/social, CRM) — not on
  engineering effort.

**Research**
- **Decision-maker auto-research returns almost nobody** — retrieval limitation, not a
  prompt or model problem. Detailed below.
- **News research is headline-only.** We removed the article-body scraper (it relied on
  an anti-bot bypass and had stopped working), so extraction works from Google News
  headlines, dates and publishers rather than full text.
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
| **Fits theme** — genuinely agentic and API-first? | **Agentic:** a real tool-calling agent that decides what to examine, exposed three ways including MCP. **API-first:** everything from SSC APIs, our own frontend, and via MCP no frontend at all. **Reimagined:** Today turns 38 signals into 3 decisions. *Weak spot: we're on PV1, not Titan* | Strong |
| **Practicality** | Real CSM problem from the actual project brief, live SSC data, honest labelling of what's placeholder | Strong |
| **Business potential** | Directly ARR-linked. Deployment config, auth and a documented POC→production path already exist | Strong |
| **Token efficiency** | ~4.4k tokens per Ask query, ~5.2k for a daily briefing, on a low-cost model. Tools return the smallest useful shape so the agent surveys cheaply and drills selectively. Token count is visible in the UI | **Probably our strongest, and most teams will ignore this criterion** |
| **Wow factor** | Three entry points, live data, visible agent reasoning, editable drafted emails, honest provenance | Good |

**Where we're genuinely weak:**
- **Not using Titan**, which the brief calls the primary target.
- **Platform usage is placeholder**, and four triggers depend on it.
- **9 of 23 triggers unbuilt** — all data-blocked, but still unbuilt.
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
