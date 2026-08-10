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

from .. import config
from . import agent

_BRIEFING_PROMPT = """Produce today's CSM worklist for this portfolio.

Survey with list_customers, then call get_customer_detail on the three accounts that
most need attention today. Base the ranking on what the data actually shows -- score
movement, signals that fired, capacity limits, stakeholder changes, recent news.

Return ONLY a JSON object in exactly this shape, no prose around it:

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

    result = agent.run([{"role": "user", "content": _BRIEFING_PROMPT}])
    # agent.run has already restored real names in `reply`.
    parsed = _extract_json(result.get("reply", ""))

    payload = {
        "date": date.today().isoformat(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "priorities": (parsed or {}).get("priorities", []),
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
