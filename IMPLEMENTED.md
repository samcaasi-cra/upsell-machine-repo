# Upsell Machine — what's built

Project 5: Customer Upsell, Retention & Decision-Making Automation.
Internal CSM-facing dashboard. Last updated: 9 August 2026.

---

## The app in one paragraph

A two-tab dashboard. **Opportunities** is the CSM's daily working view: a categorised
board of engagement signals per customer, each card carrying a drafted email you can
edit and send. **Customers** is the drill-down: per-account SSC score history, platform
usage, tracked decision-makers, and tracked news. Signals come from live
SecurityScorecard data, automated web research, and (for platform usage only)
placeholder data pending a real feed.

---

## Data provenance — important for demos

The UI labels this everywhere, but to be explicit:

| Data | Source | Status |
|---|---|---|
| SSC scores, grades, industry, score history | SecurityScorecard API | **Live** |
| Third-party supplier detection + their scores | SecurityScorecard API | **Live** |
| Customer roster | `backend/data/customers.json` + SSC portfolio sync | **Live** |
| News events (acquisitions, offices, launches) | Google News RSS + web scrape → OpenAI extraction | **Live, cached** |
| Decision-makers / job titles | Research prompt run in Claude, pasted back | **Live, cached** |
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
  customer. Google News RSS primary, DuckDuckGo scrape for article text, OpenAI
  extracts structured JSON.
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

### Suggested walkthrough

1. **Opportunities board** — lead here. Point out the provenance legend, then the account
   chips (live SSC grades) and the four lanes.
2. **Open a card** → drafted email with the right recipient resolved from real research.
   Change the recipient in the dropdown, show the greeting re-point, edit the body,
   reset to default.
3. **Point at a `◇ Sample data` card** — say plainly which parts are placeholder and why
   they're labelled.
4. **Customers tab** → a customer detail: live SSC score chart, then the News panel
   showing automatically-researched events.
5. **Back to the board, tick "Show unbuilt triggers as concepts"** — the board becomes
   the full 23-trigger vision. Each concept card names the trigger and the exact data
   source it's waiting on, which turns "what's missing" into a concrete shopping list.
6. **Close on the architecture point**: every gap is a connection, not a rebuild — news
   already made exactly that transition from manual to automated with no prompt or
   parser changes.

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
- **DuckDuckGo rate-limits** after modest use. News degrades rather than breaks because
  Google News RSS carries it, but the article-text half goes quiet.
- **Decision-maker auto-research returns almost nobody** — retrieval limitation, not a
  prompt or model problem. Detailed below.
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

## What would move this furthest, fastest

1. **A real platform-usage feed.** Biggest sample-data surface — would make triggers
   1, 3, 10, 21 genuinely live.
2. **Salesforce access.** Unblocks #23 and replaces sample sponsor/CSM data.
3. **Per-customer supplier portfolios in SSC.** Unblocks #14 and #15.
4. **An agreed ROI model.** Unblocks #9, which is the strongest renewal-conversation
   asset in the whole list.
