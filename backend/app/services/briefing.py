"""The agent's daily briefing: three things to do today, in order.

This is the difference between a dashboard and an agentic workflow. A dashboard hands
you thirty-eight signals and makes you the reasoning engine. This asks the agent to do
the reasoning and hand back a short ranked worklist with the outreach already drafted --
you approve or skip rather than scan and decide.

Cached per calendar day. The briefing costs a few thousand tokens to produce and the
underlying signals don't change minute to minute, so recomputing it on every page load
would be waste dressed up as freshness. "Refresh" forces a rebuild when you want one.
"""

import json
import re
from datetime import date, datetime, timezone
from typing import Optional

from .. import config, storage
from . import agent

_BRIEFING_PROMPT = """Produce today's CSM worklist for this portfolio.

Survey with list_customers, then call get_customer_detail on the three accounts that
most need attention today. Base the ranking on what the data actually shows -- score
movement, signals that fired, capacity limits, stakeholder changes, recent news.

For each of the three, once you've drafted its outreach, call queue_outreach with that
draft and your one-sentence reflection before moving on to the next one -- don't wait
until the end to queue all three.

After all three are queued, return ONLY a JSON object in exactly this shape, no prose
around it:

{
  "priorities": [
    {
      "customer": "the CUST_ label",
      "headline": "six words or fewer on why this is today's priority",
      "why": "one or two sentences citing the specific numbers you saw",
      "action": "the single concrete next step, imperative mood",
      "email_subject": "subject line for that outreach",
      "email_body": "3-5 short sentences. Specific, no hype, no 'I hope this finds you well'."
    }
  ]
}

Exactly three entries, most urgent first."""


def _cache_file():
    return config.DATA_DIR / "briefing.json"


def load_cached() -> Optional[dict]:
    path = _cache_file()
    if not path.exists():
        return None
    try:
        cached = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if cached.get("date") != date.today().isoformat():
        return None
    return cached


def _save(payload: dict) -> None:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    _cache_file().write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _extract_json(text: str) -> Optional[dict]:
    """The model is asked for bare JSON but sometimes wraps it in a fence or prose."""
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    candidate = fenced.group(1) if fenced else text
    start, end = candidate.find("{"), candidate.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        return json.loads(candidate[start : end + 1])
    except json.JSONDecodeError:
        return None


def build(force: bool = False) -> dict:
    """Return today's briefing, from cache unless forced."""
    if not force:
        cached = load_cached()
        if cached:
            return cached

    existing_action_ids = {a.id for a in storage.load_queued_actions()}
    result = agent.run([{"role": "user", "content": _BRIEFING_PROMPT}])
    # agent.run has already restored real names in `reply`.
    parsed = _extract_json(result.get("reply", ""))

    # Match each priority to the queued action the agent created for it, so the
    # worklist can show its own reflection alongside the draft rather than the two
    # living in separate places.
    new_actions = [a for a in storage.load_queued_actions() if a.id not in existing_action_ids]
    priorities = (parsed or {}).get("priorities", [])
    for p in priorities:
        match = next(
            (a for a in new_actions if a.customer_name.strip().lower() == str(p.get("customer", "")).strip().lower()),
            None,
        )
        p["queued"] = match is not None
        p["action_id"] = match.id if match else None
        p["reflection"] = match.reasoning if match else None
        if match:
            # The JSON summary asks the model to redraft the email a second time, and
            # that redraft isn't guaranteed to restore real names as reliably as the
            # queue_outreach call already did (verified -- see agent._prepare_tool_args).
            # Show the queued, already-verified text rather than trusting a second draft.
            p["email_subject"] = match.subject
            p["email_body"] = match.body

    payload = {
        "date": date.today().isoformat(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "priorities": priorities,
        "tokens": result.get("tokens", {}),
        "provider": result.get("provider"),
        "model": result.get("model"),
        "tool_calls": [t["tool"] for t in result.get("tool_calls", [])],
        "pseudonymised": result.get("pseudonymised", False),
    }
    if not payload["priorities"]:
        # Surface the raw reply rather than silently showing an empty screen.
        payload["error"] = "The agent didn't return a usable worklist."
        payload["raw_reply"] = result.get("reply", "")[:600]

    _save(payload)
    return payload
