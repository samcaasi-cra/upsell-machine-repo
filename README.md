# Gaia ARR Growth Agent — Project 5

Watches a SecurityScorecard portfolio and tells a CSM which accounts to act on and what
to say. Built on SSC APIs, with no SSC frontend involved.

- **The board** — every signal we can detect, in four lanes, each card carrying a
  drafted email with the recipient already resolved
- **Daily research** — searches the news for every account and extracts structured
  events, unattended, once a day
- **MCP server** — the same portfolio tools in any MCP client, no interface of ours
  needed

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
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000
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

The app is a single **Opportunities board**.

**Four lanes** — *Own Cyber Posture*, *Usage*, *Suppliers*, *News*. Each card leads with
a short instruction; click the info icon for the fuller explanation behind it.

**Click any card** for the drafted email: editable subject and body, a recipient
dropdown covering every tracked decision-maker, reset-to-default, and copy. News cards
also carry a link to the source article, which is appended to the email.

**Customer picker** filters the board to the accounts you care about. **View modes**
(Default / Detailed / Compact) and the text-size control adjust density.

**Provenance icons** in the legend explain where each kind of data comes from. Tick
**"Show unbuilt triggers as concepts"** for illustrative cards covering the triggers
that aren't built yet — each names the data source it's waiting on.

**"Auto-researched <date> · Run now"** is the daily research agent. It runs once per day
while the backend is up; the button forces a run.

### Reaching the agent

The tool-calling agent isn't linked from the board. Two ways in:

- **MCP** — connect Claude Desktop to the same tools and work the portfolio
  conversationally. See [MCP.md](MCP.md). This is the recommended path.
- **The API** — `POST /agent/chat` for questions, `GET /today` for a ranked worklist
  with drafted emails.

Both need `OPENAI_API_KEY` (or `ANTHROPIC_API_KEY`).

### Research

Two ways to populate decision-makers and news:

- *Auto-research* (needs `OPENAI_API_KEY`) — searches and extracts automatically. Works
  well for news; rarely finds decision-makers, see IMPLEMENTED.md for why.
- *Manual* — generates a prompt you run in Claude yourself, then paste the JSON back.
  This is the better path for decision-makers.

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
    services/    SSC client, research, signal logic, scheduler, agent
    models.py    Pydantic schemas shared across the API
    storage.py   JSON-file persistence
  data/          Customer roster + research caches (caches are gitignored)
  demo.py        Snapshot/restore for demos
  mcp_server.py  The tools over Model Context Protocol
frontend/
  src/
    components/  Board, customer picker, email drawer, controls
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
