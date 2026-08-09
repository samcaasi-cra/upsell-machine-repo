"""Once-a-day automated news research across the whole customer roster.

Runs inside the FastAPI process as a background asyncio task. Deliberately simple --
no external scheduler or job queue for a hackathon-scale app:

- The last completed run date is persisted, so restarting the server doesn't
  re-trigger a run that already happened today.
- Customers are processed sequentially with a delay between them, because the
  underlying web search rate-limits under bursty load.
- Only news research is batched. Decision-maker research is left manual: public
  search rarely names a company's security leadership, so an unattended run mostly
  produces nothing (see the note in routers/decision_makers.py).
"""

import asyncio
import json
from datetime import date, datetime, timezone
from typing import Optional

from .. import config, storage
from ..models import NewsEvent
from . import news_prompt, web_research

_CHECK_INTERVAL_SECONDS = 60 * 30  # re-check every 30 min whether today's run is due
_DELAY_BETWEEN_CUSTOMERS_SECONDS = 20  # be gentle with the search backends

_state_lock = asyncio.Lock()
_running = False


def _state_file():
    return config.DATA_DIR / "research_schedule.json"


def load_state() -> dict:
    path = _state_file()
    if not path.exists():
        return {"last_run_date": None, "last_run_at": None, "last_result": None}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"last_run_date": None, "last_run_at": None, "last_result": None}


def _save_state(state: dict) -> None:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    _state_file().write_text(json.dumps(state, indent=2), encoding="utf-8")


def is_running() -> bool:
    return _running


def status() -> dict:
    state = load_state()
    return {
        "enabled": web_research.is_configured(),
        "running": _running,
        "last_run_date": state.get("last_run_date"),
        "last_run_at": state.get("last_run_at"),
        "last_result": state.get("last_result"),
        "due_today": state.get("last_run_date") != date.today().isoformat(),
    }


def _merge_news(customer, new_events: list[NewsEvent]) -> int:
    """Merge into the cache the same way the manual import does. Returns how many
    genuinely new events were added."""
    previous = storage.load_news_events(customer.domain)
    merged: list[NewsEvent] = list(previous.events) if previous else []
    seen = {(e.event_type, e.headline.strip().lower()) for e in merged}
    added = 0
    for event in new_events:
        key = (event.event_type, event.headline.strip().lower())
        if key not in seen:
            merged.append(event)
            seen.add(key)
            added += 1
    if added:
        merged.sort(key=lambda e: e.date, reverse=True)
        storage.save_news_events(customer.domain, merged)
    return added


async def run_batch(reason: str = "scheduled") -> dict:
    """Research news for every customer. Safe to call concurrently -- a second caller
    gets a 'already running' result rather than doubling the API spend."""
    global _running
    async with _state_lock:
        if _running:
            return {"status": "already_running"}
        _running = True

    started = datetime.now(timezone.utc)
    customers = storage.load_customers()
    total_added = 0
    failures = 0

    try:
        for i, customer in enumerate(customers):
            prompt = news_prompt.build_prompt(customer.name, customer.domain, None)
            queries = [
                f"{customer.name} acquisition OR acquires OR merger",
                f"{customer.name} opens new office OR expands to",
                f"{customer.name} launches new product OR service",
            ]
            try:
                raw = await asyncio.to_thread(
                    web_research.research_to_json, prompt, queries, "m", True
                )
                if raw:
                    total_added += _merge_news(customer, news_prompt.parse_import(raw))
            except Exception:
                failures += 1

            if i < len(customers) - 1:
                await asyncio.sleep(_DELAY_BETWEEN_CUSTOMERS_SECONDS)

        result = {
            "reason": reason,
            "customers_processed": len(customers),
            "events_added": total_added,
            "failures": failures,
            "duration_seconds": round((datetime.now(timezone.utc) - started).total_seconds()),
        }
        _save_state(
            {
                "last_run_date": date.today().isoformat(),
                "last_run_at": started.isoformat(),
                "last_result": result,
            }
        )
        return result
    finally:
        _running = False


async def daily_loop() -> None:
    """Background loop: run once per calendar day, whenever the server happens to be up."""
    while True:
        try:
            if web_research.is_configured():
                state = load_state()
                if state.get("last_run_date") != date.today().isoformat():
                    await run_batch(reason="scheduled")
        except Exception:
            pass  # never let a bad run kill the loop
        await asyncio.sleep(_CHECK_INTERVAL_SECONDS)
