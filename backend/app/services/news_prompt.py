"""Generates a copy/paste research prompt for triggers #2, #5, #6 (acquisition
announced, new offices/regional operations, new product/service launch) and parses
the JSON pasted back in. Same pattern as decision_maker_prompt.py: no LLM API is
called here -- the user runs this prompt themselves in Claude and pastes the result
back in via the import endpoint.
"""

import json
import re
from typing import List, Optional

from ..models import NewsEvent

_JSON_SCHEMA_HINT = """{
  "events": [
    {
      "event_type": "acquisition | new_office | product_launch",
      "headline": "Short factual headline",
      "date": "YYYY-MM-DD (best known date -- publication or announcement date)",
      "summary": "1-2 sentence factual summary of what happened",
      "source_url": "https://... or null if not reliably known"
    }
  ]
}"""


def build_prompt(company_name: str, domain: str, existing_headlines: Optional[List[str]] = None) -> str:
    existing_block = "(none supplied)"
    if existing_headlines:
        existing_block = "\n".join(f"- {h}" for h in existing_headlines)

    return f"""Research recent public news about this company using only public sources
(company press releases, reputable news outlets, official announcements).

COMPANY: {company_name}
DOMAIN: {domain}

ALREADY KNOWN HEADLINES (do not repeat these, only report genuinely new events):
{existing_block}

TARGET EVENT TYPES -- only these three, nothing else:
1. acquisition -- this company acquiring another company, or being acquired/merged.
2. new_office -- this company announcing a new office, region, or physical operation.
3. product_launch -- this company launching a new product or service.

RULES
- Only include an event if there is clear, current public evidence it happened, ideally
  within the last 6 months. If you are not confident of the date, use your best estimate
  and say so in the summary rather than guessing a precise date.
- Do not include rumours, speculation, or "reportedly considering" stories -- confirmed
  events only.
- Do not include events unrelated to the three target types (e.g. general financial
  results, hiring announcements, awards, opinion pieces).
- If nothing qualifies for a given type, simply omit it -- do not invent an event to
  fill a category.
- Maximum 5 events total. If more than 5 qualify, keep the most recent and most
  significant.
- For each event, identify the single best source URL if one is reliably known.

OUTPUT FORMAT -- IMPORTANT
Return ONLY a single JSON object matching this exact shape, no prose before or after it,
no markdown code fences:

{_JSON_SCHEMA_HINT}

If no qualifying events are found, return {{"events": []}}."""


def parse_import(raw_text: str) -> List[NewsEvent]:
    """Parse the JSON a user pastes back from running the prompt above. Tolerates
    markdown code fences since that's how it usually gets copied out of a chat."""
    text = raw_text.strip()
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence_match:
        text = fence_match.group(1).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"That doesn't look like valid JSON: {exc}") from exc

    if isinstance(data, dict) and "events" in data:
        events_raw = data["events"]
    elif isinstance(data, list):
        events_raw = data
    else:
        raise ValueError('Expected a JSON object with an "events" array, or a JSON array of events.')

    if not isinstance(events_raw, list):
        raise ValueError('The "events" field must be a list (it can be empty).')

    events: List[NewsEvent] = []
    for i, item in enumerate(events_raw):
        try:
            events.append(NewsEvent(**item))
        except Exception as exc:
            raise ValueError(f"Event #{i + 1} doesn't match the expected shape: {exc}") from exc
    return events
