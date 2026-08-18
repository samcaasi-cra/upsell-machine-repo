# Gaia ARR Growth Agent — Project 5

An **AI agent that helps CSMs upsell existing customers** (e.g. from Titan Watch to
Titan MAX) — built on SecurityScorecard APIs, with no SSC frontend involved.

The app is called **Gaia**, and the nav has four tabs, each a wide, descriptively-labelled
button rather than a short tab name:

1. **All Growth Signals** — the main board, every signal across the portfolio, grouped
   into four lanes: **Change in score** (evidence the customer's own security is
   already paying off), **Change in Usage** (platform usage telling you the account is
   ready for more), **Change in Risk** (third-party and sector risk), and **Change at
   Customer** (personnel changes, company news, and relationship signals like email,
   CRM, tickets and surveys).
2. **Today** — the agent's ranked daily worklist, three drafted actions.
3. **Ask** — a conversational agent over live portfolio data; the conversation persists
   across tab switches instead of resetting.
4. **Joint Success Plan** — per-customer objective and agreed target metric, plus a
   30-day feed of what's actually changed, sorted by what needs attention first.

Each opportunity card leads with a short, active-voice instruction ("Warn them: X is
showing elevated risk"); the fuller explanation is a click away, not shown by default.
A settings menu (gear icon, top right) holds the CSM/Customer view toggle, the
Default/Detailed/Compact density toggle, and the text-size control, and a
search/multi-select picker (with customer logos) narrows the board to specific accounts
instead of scanning everyone. All four tabs' data loads in parallel as soon as the app
opens, so switching between them is instant rather than triggering a fresh fetch.

Behind the board, **daily research** runs unattended: once a day it searches the news
for every account and extracts structured events. And an **MCP server** exposes the same
portfolio tools to any MCP client, so a CSM can work the portfolio with no interface of
ours involved. See [MCP.md](MCP.md).

**Customers** (per-account drill-down) is still fully implemented in the codebase —
backend endpoints and frontend components both — but isn't wired into the nav. See
[frontend/src/App.tsx](frontend/src/App.tsx) if you want to bring it back.

- **[IMPLEMENTED.md](IMPLEMENTED.md)** — what's built, trigger coverage, data
  provenance, limitations, criteria self-assessment. Start here if you're reviewing.
- **[MCP.md](MCP.md)** — connecting Claude Desktop to the tools.
- **[DEPLOY.md](DEPLOY.md)** — putting it on a URL for the team (Render).
- **[deploy_to_pythonanywhere.md](deploy_to_pythonanywhere.md)** — same, on PythonAnywhere instead.

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

# macOS/Linux
.venv/bin/python -m pip install -r requirements.txt

# Windows
.venv\Scripts\python -m pip install -r requirements.txt
```

### 2. Credentials

Copy the example and fill it in:

```bash
cp backend/.env.example backend/.env
```

| Variable | Required | What it does |
|---|---|---|
| `API_KEY` | **Yes** | SecurityScorecard. Nothing works without it. |
| `OPENAI_API_KEY` | No | Enables automated research and the agent. Without it, research falls back to copy/paste and the agent endpoints explain what's missing. |
| `CSM_NAME` | No | Who the app greets and who signs drafted emails. Defaults to `Alex`. |
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

# macOS/Linux
.venv/bin/python -m uvicorn app.main:app --reload --port 8000

# Windows
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — frontend:**
```bash
cd frontend
npm run dev
```

Then open **http://localhost:5173**.

The frontend expects the backend on port **8000** and the backend allows CORS from
**5173**, so keep both ports as they are unless you change both ends.

The first load takes a few seconds — the board fans out to SecurityScorecard for every
customer. Responses are cached for 10 minutes, so it's instant after that.

To check the backend on its own: http://localhost:8000/health should return
`{"status":"ok","auth_required":false,"csm_name":"Alex"}`. Interactive API docs are at
http://localhost:8000/docs.

---

## Using it

**All Growth Signals** is the landing screen — every signal, across the four lanes
described above. A few things to know:

- Each card shows a short, active-voice instruction by default (e.g. "Send them an
  automated quote to upgrade before they hit the cap."). Click the **ⓘ** to see the
  fuller explanation, or switch to the **Detailed** view (settings menu) to show it
  inline for every card.
- The **settings menu** (gear icon, top right) holds three groups: **Viewing as**
  (CSM / Customer — Customer hides pricing and discount cards), **Density**
  (Default / Detailed / Compact — Compact fits far more per lane without scrolling),
  and **text size** (A− / A+). All three persist across reloads.
- **Select customers** searches and multi-selects accounts (with logos, falling back to
  initials avatars when a domain has no logo) to narrow the board — the default with
  nothing selected is "Showing all customers."
- Click a card for an editable drafted email with a recipient dropdown. News cards also
  carry a link to the source article, which is appended to the email.
- The **provenance legend** (icons explaining where each kind of data comes from, plus
  the *"Show unbuilt triggers as concepts"* toggle for illustrative cards) sits at the
  **bottom** of the board, below the four lanes.
- **View in SecurityScorecard** links out to the team's portfolio in the SSC platform.
- The name signing each drafted email comes from `CSM_NAME`.

**"Auto-researched &lt;date&gt; · Run now"** in the top bar is the daily research agent. It
runs once per day while the backend is up; the button forces a run.

**Today**, **Ask**, and **Joint Success Plan** are full tabs in the nav (see above) —
`POST /agent/chat` and `GET /today` are also reachable directly over the API, and the
same tools are exposed over MCP ([MCP.md](MCP.md)) for working the portfolio from
Claude Desktop with no UI of ours involved. **Customers** (per-account drill-down: SSC
score chart, usage breakdown, tracked decision-makers and news, "Add customer" / "Sync
from portfolio") is likewise still implemented but not in the nav. All of the
agent-backed views need `OPENAI_API_KEY` (or `ANTHROPIC_API_KEY`).

**Research** — two ways to populate decision-makers and news:

- *Auto-research* (needs `OPENAI_API_KEY`) — searches and extracts automatically. Works
  well for news; rarely finds decision-makers, see IMPLEMENTED.md for why.
- *Manual* — generates a prompt you run in Claude yourself, then paste the JSON back.
  This is the better path for decision-makers.

---

## Demo safety net

Live research is non-deterministic, so don't let a demo depend on it succeeding:

macOS/Linux:
```bash
cd backend
.venv/bin/python demo.py snapshot   # capture a good state
.venv/bin/python demo.py status     # compare live vs baseline
.venv/bin/python demo.py restore    # roll back, then restart the backend
```

Windows:
```bash
cd backend
.venv\Scripts\python demo.py snapshot
.venv\Scripts\python demo.py status
.venv\Scripts\python demo.py restore
```

---

## Layout

```
backend/
  app/
    routers/     HTTP endpoints
    services/    SSC client, research, signal logic, scheduler, agent
    models.py    Pydantic schemas shared across the API
    storage.py   JSON-file persistence
  data/          Customer roster + research caches (caches are gitignored)
  demo.py        Snapshot/restore for demos
  mcp_server.py  The tools over Model Context Protocol
frontend/
  src/
    components/
      OpportunityBoard.tsx   All Growth Signals -- the main board
      TodayView.tsx          Today -- agent-ranked daily worklist
      AgentChat.tsx          Ask -- conversational agent, stays mounted across tabs
      SuccessPlanView.tsx    Joint Success Plan -- target metric + 30-day change feed
      SettingsMenu.tsx       CSM/Customer, density and text-size controls, gear-icon menu
      Spinner.tsx            Shared no-text loading indicator
      CustomerPicker.tsx     Search + multi-select customer filter, with logos
      CustomerLogo.tsx       Clearbit logo lookup, initials-avatar fallback
      BoardControls.tsx      Default/Detailed/Compact + text-size controls (used by SettingsMenu)
      InfoPopover.tsx        Click-to-reveal detail affordance ("ⓘ")
      icons.tsx              Small inline SVG icon set
      EmailDrawer.tsx        Editable drafted email for a card
      CustomerTable.tsx, CustomerDetail.tsx, ...  Customers view (not in the nav, see above)
    api/client.ts
```

---

## Troubleshooting

**Board is empty / "Failed to load".** Backend isn't running, or `API_KEY` is missing
from `backend/.env`. Check http://localhost:8000/health.

**Cards show but details are blank.** The backend is running older code than the
frontend expects — restart it. Use `--reload` so it picks changes up automatically.

**A customer shows "Score unavailable".** That domain isn't resolving in
SecurityScorecard — usually a typo in the domain, or a domain SSC doesn't track.

**Console shows repeated `ERR_NAME_NOT_RESOLVED`.** Company logos are fetched from
`logo.clearbit.com`, which doesn't resolve here. Harmless — every card falls back to an
initials avatar. Known, and left alone deliberately.

**Auto-research is unavailable.** No `OPENAI_API_KEY` in `.env`. Expected — use the
copy/paste flow.

**Auto-research says "no new events found".** Working correctly — it found nothing new
since last time. It dedupes against what's already cached.

**A login screen appears locally.** `APP_PASSWORD` is set in your `.env` — clear it for
local development.
