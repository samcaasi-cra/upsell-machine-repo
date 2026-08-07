# Upsell Machine — Project 5 Dashboard

Live dashboard for Cyber Rescue's Customer Upsell, Retention & Decision-Making
Automation project. See `.claude/plans` history or ask Claude for the original design
plan (`precious-gathering-marble.md`).

## What's real vs. mock

- **SSC scores**: live, via the SecurityScorecard API (`backend/app/services/ssc_client.py`).
  Uses one shared portfolio in the real Cyber Rescue SSC account, named
  `Upsell Machine Dashboard - Demo Domains - Do Not Delete` — do not delete it, other
  customer domains added through the UI get added to it automatically.
- **Decision-makers (job titles / LinkedIn)**: manual loop, no API key needed. Open a
  customer, click "Research decision-makers", copy the generated prompt, run it in
  Claude yourself, paste the JSON result back in.
- **Platform usage** (slots filled, reports generated, visits): sample data, clearly
  labeled in the UI. Swap in real data by replacing `backend/app/services/mock_usage.py`.
- **CRM / sponsor-CSM data**: sample roster in `backend/data/customers.json`, editable
  via the UI's "Add customer" button or by hand.

## Running it

Backend (FastAPI):
```bash
cd backend
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000
```
First run: `python -m venv .venv && .venv/Scripts/python -m pip install -r requirements.txt`.
Requires `backend/.env` with `API_KEY=<your SecurityScorecard API key>` (see `.env.example`).

Frontend (Vite + React):
```bash
cd frontend
npm install   # first run only
npm run dev
```
Open http://localhost:5173 (backend must be running at http://localhost:8000).
