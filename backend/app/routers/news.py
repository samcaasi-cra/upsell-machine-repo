from fastapi import APIRouter, HTTPException

from .. import storage
from ..models import Customer, NewsEvent, NewsEventsImportRequest, NewsRecord
from ..services import news_prompt, web_research

router = APIRouter(prefix="/customers", tags=["news"])


def _merge_and_save(customer: Customer, new_events: list[NewsEvent]) -> NewsRecord:
    """News events accumulate over time (each import reports only genuinely new events,
    per the prompt's instructions) rather than replacing the prior snapshot."""
    previous = storage.load_news_events(customer.domain)
    merged: list[NewsEvent] = list(previous.events) if previous else []
    seen = {(e.event_type, e.headline.strip().lower()) for e in merged}
    for event in new_events:
        key = (event.event_type, event.headline.strip().lower())
        if key not in seen:
            merged.append(event)
            seen.add(key)
    merged.sort(key=lambda e: e.date, reverse=True)
    return storage.save_news_events(customer.domain, merged)


def _require_customer(customer_id: str) -> Customer:
    customer = storage.get_customer(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.get("/{customer_id}/news", response_model=NewsRecord)
def get_news(customer_id: str) -> NewsRecord:
    customer = _require_customer(customer_id)
    record = storage.load_news_events(customer.domain)
    return record or NewsRecord(domain=customer.domain, events=[])


@router.get("/{customer_id}/news/prompt")
def get_news_prompt(customer_id: str) -> dict:
    customer = _require_customer(customer_id)
    existing = storage.load_news_events(customer.domain)
    existing_headlines = [e.headline for e in existing.events] if existing else None
    prompt = news_prompt.build_prompt(customer.name, customer.domain, existing_headlines)
    return {"prompt": prompt}


@router.post("/{customer_id}/news/import", response_model=NewsRecord)
def import_news(customer_id: str, payload: NewsEventsImportRequest) -> NewsRecord:
    customer = _require_customer(customer_id)

    if payload.events is not None:
        new_events = payload.events
    elif payload.text is not None:
        try:
            new_events = news_prompt.parse_import(payload.text)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    else:
        raise HTTPException(status_code=400, detail="Provide either 'text' or 'events'.")

    return _merge_and_save(customer, new_events)


@router.post("/{customer_id}/news/auto-research", response_model=NewsRecord)
def auto_research_news(customer_id: str) -> NewsRecord:
    """Automated alternative to the copy/paste flow: searches and scrapes the web, then
    has OpenAI extract the same JSON shape the manual flow produces."""
    customer = _require_customer(customer_id)
    if not web_research.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Auto-research needs an OPENAI_API_KEY in backend/.env. Use the copy/paste flow instead.",
        )

    existing = storage.load_news_events(customer.domain)
    existing_headlines = [e.headline for e in existing.events] if existing else None
    prompt = news_prompt.build_prompt(customer.name, customer.domain, existing_headlines)

    queries = [
        f"{customer.name} acquisition OR acquires OR merger",
        f"{customer.name} opens new office OR expands to",
        f"{customer.name} launches new product OR service",
    ]
    try:
        raw = web_research.research_to_json(prompt, queries, recency="m")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Auto-research failed: {exc}") from exc

    if raw is None:
        return existing or NewsRecord(domain=customer.domain, events=[])

    try:
        new_events = news_prompt.parse_import(raw)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=f"Could not parse the research result: {exc}") from exc

    return _merge_and_save(customer, new_events)
