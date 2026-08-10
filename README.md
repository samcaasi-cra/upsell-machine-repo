# Upsell Machine — Project 5

Internal CSM dashboard for Cyber Rescue's *Customer Upsell, Retention &
Decision-Making Automation* project. Surfaces per-customer engagement signals — SSC
score movement, platform usage, decision-maker changes, company news — and drafts an
email for each one.

- **[IMPLEMENTED.md](IMPLEMENTED.md)** — what's built, trigger coverage, data
  provenance, limitations. Start here if you're reviewing the project.
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

**Opportunities** — the main working view. Four lanes of signals across all customers.
Click any card for a drafted email you can edit, re-address, and copy. Account chips
filter the board. Tick *"Show unbuilt triggers as concepts"* to see illustrative cards
for the triggers that aren't built yet.

**Customers** — per-account detail: SSC score chart, usage breakdown, tracked
decision-makers, tracked news. "Add customer" adds one by hand; "Sync from portfolio"
imports anything added directly in the SecurityScorecard UI.

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
    components/  Board, customer views, email drawer, modals
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
