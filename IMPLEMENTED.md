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

Cards built on sample data carry a dashed `◇ Sample data` tag on the card and in the
email drawer. The Opportunities board has a provenance legend; the Customers table
marks each column `● live SSC` / `◆ researched` / `◇ sample`.

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

---

## Known limitations

- **DuckDuckGo rate-limits** under repeated use. Google News RSS keeps working, so news
  research degrades rather than breaks.
- **Decision-maker auto-research rarely returns anyone.** Not a bug — see below.
- **Actioned state is session-only**, cleared on reload. Deliberate: matches the
  reference demo, and there's no per-user identity to attribute it to yet.
- **The scheduler runs in-process**, so it only fires while the backend is up. Fine for
  a hackathon; a real deployment wants cron or a task queue.

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
