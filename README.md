# Gaia ARR Growth Agent — Project 5

An **AI agent that helps CSMs upsell existing customers** (e.g. from Titan Watch to
Titan MAX) — built on SecurityScorecard APIs, with no SSC frontend involved.

The main interface is the **Opportunities** board: every signal across the portfolio,
grouped into four lanes —

- **Own Cyber Posture** — evidence the customer's own security is already paying off
- **Usage** — platform usage telling you the account is ready for more
- **Suppliers** — third-party and sector risk detected outside the customer's own score
- **News** — company news and people moments worth a direct, timely touch

Each card leads with a short, active-voice instruction ("Warn them: X is showing
elevated risk"); the fuller explanation is a click away, not shown by default. A
**Default / Detailed / Compact** toggle and a text-size control let a CSM pick how
much detail is on screen at once, and a search/multi-select picker (with customer
logos) narrows the board to specific accounts instead of scanning everyone.

It also reaches you via an **MCP server** — the same tools in any MCP client, no
interface of ours needed. See [MCP.md](MCP.md).

The **Today** (agent-drafted daily priorities), **Ask** (plain-English portfolio Q&A),
and **Customers** (per-account drill-down) views are still fully implemented in the
codebase — backend endpoints and frontend components both — but aren't wired into the
nav, since Opportunities is the one view CSMs use day to day. See
[frontend/src/App.tsx](frontend/src/App.tsx) if you want to bring one back.

- **[IMPLEMENTED.md](IMPLEMENTED.md)** — what's built, trigger coverage, data
  provenance, limitations, criteria self-assessment. Start here if you're reviewing.
- **[MCP.md](MCP.md)** — connecting Claude Desktop to the tools.
- **[DEPLOY.md](DEPLOY.md)** — putting it on a URL for the team.

---

## Prerequisites

- **Python 3.12** (verified on 3.12.6)
- **Node 20+** (verified on 25.2.1)
- A **SecurityScorecard API key**

---

## First-time setup

### 1. Backend

```bash
cd backend
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
```

On macOS/Linux use `.venv/bin/python` in place of `.venv/Scripts/python` throughout.

### 2. Credentials

Copy the example and fill it in:

```bash
cp backend/.env.example backend/.env
```

| Variable | Required | What it does |
|---|---|---|
| `API_KEY` | **Yes** | SecurityScorecard. Nothing works without it. |
| `OPENAI_API_KEY` | No | Enables the "Auto-research" buttons. Without it those disable and the copy/paste research flow still works. |
| `APP_PASSWORD` | No | Adds a login screen. **Leave blank locally**; only set it when deploying. |

### 3. Frontend

```bash
cd frontend
npm install
```

---

## Running it

Two terminals.

**Terminal 1 — backend:**
```bash
cd backend
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — frontend:**
```bash
cd frontend
npm run dev
```

Then open **http://localhost:5173**.

The first load takes a few seconds — the board fans out to SecurityScorecard for every
customer. Responses are cached for 10 minutes, so it's instant after that.

To check the backend on its own: http://localhost:8000/health should return
`{"status":"ok","auth_required":false}`. Interactive API docs are at
http://localhost:8000/docs.

---

## Using it

**Opportunities** is the landing screen and the only view in the nav — every signal,
across four lanes (Own Cyber Posture, Usage, Suppliers, News). A few things to know:

- Each card shows a short, active-voice instruction by default (e.g. "Flag rising slot
  usage before it hits the licensed cap."). Click the **ⓘ** to see the fuller
  explanation, or switch to the **Detailed** view to show it inline for every card.
- **Default / Detailed / Compact** (top right) trade off how much is on screen at once;
  Compact fits far more per lane without scrolling. **A− / A+** scales text size. Both
  choices persist across reloads.
- **Select customers** searches and multi-selects accounts (with logos, falling back to
  initials avatars when a domain has no logo) to narrow the board — the default with
  nothing selected is "Showing all customers."
- Click a card for an editable drafted email with a recipient dropdown. Tick *"Show
  unbuilt triggers as concepts"* for illustrative cards covering triggers that aren't
  built yet.
- **View in SecurityScorecard** links out to the team's portfolio in the SSC platform.

**MCP** — connect Claude Desktop to the same tools and skip the UI entirely.
See [MCP.md](MCP.md).

**Today** and **Ask** (agent-drafted daily priorities and plain-English portfolio Q&A)
still work if you wire them back into the nav — both need `OPENAI_API_KEY` (or
`ANTHROPIC_API_KEY`) to function. **Customers** (per-account drill-down: SSC score
chart, usage breakdown, tracked decision-makers and news, "Add customer" / "Sync from
portfolio") is likewise still implemented but not in the nav.

**Research** — two ways to populate decision-makers and news:
- *Auto-research* (needs `OPENAI_API_KEY`) — searches and extracts automatically. Works
  well for news; rarely finds decision-makers, see IMPLEMENTED.md for why.
- *Manual* — generates a prompt you run in Claude yourself, then paste the JSON back.
  This is the better path for decision-makers.

News research also runs automatically once per day while the backend is up.

---

## Demo safety net

Live research is non-deterministic, so don't let a demo depend on it succeeding:

```bash
cd backend
.venv/Scripts/python demo.py snapshot   # capture a good state
.venv/Scripts/python demo.py status     # compare live vs baseline
.venv/Scripts/python demo.py restore    # roll back, then restart the backend
```

---

## Layout

```
backend/
  app/
    routers/     HTTP endpoints
    services/    SSC client, research, signal logic, scheduler
    models.py    Pydantic schemas shared across the API
    storage.py   JSON-file persistence
  data/          Customer roster + research caches (caches are gitignored)
  demo.py        Snapshot/restore for demos
frontend/
  src/
    components/
      OpportunityBoard.tsx   The main (and only nav'd) view
      CustomerPicker.tsx     Search + multi-select customer filter, with logos
      CustomerLogo.tsx       Clearbit logo lookup, initials-avatar fallback
      BoardControls.tsx      Default/Detailed/Compact + text-size controls
      InfoPopover.tsx        Click-to-reveal detail affordance ("ⓘ")
      icons.tsx              Small inline SVG icon set
      EmailDrawer.tsx        Editable drafted email for a card
      TodayView.tsx, AgentChat.tsx, CustomerTable.tsx,
      CustomerDetail.tsx, ...  Today/Ask/Customers views (not in the nav, see above)
    api/client.ts
```

---

## Troubleshooting

**Board is empty / "Failed to load".** Backend isn't running, or `API_KEY` is missing
from `backend/.env`. Check http://localhost:8000/health.

**A customer shows "Score unavailable".** That domain isn't resolving in
SecurityScorecard — usually a typo in the domain, or a domain SSC doesn't track.

**Auto-research buttons are greyed out.** No `OPENAI_API_KEY` in `.env`. Expected —
use the copy/paste flow.

**Auto-research says "no new events found".** Working correctly — it found nothing new
since last time. It dedupes against what's already cached.

**Auto-research fails with a search error.** DuckDuckGo rate-limits after repeated use.
Wait a while, or use the copy/paste flow. News research still works via Google News.

**A login screen appears locally.** `APP_PASSWORD` is set in your `.env` — clear it for
local development.
