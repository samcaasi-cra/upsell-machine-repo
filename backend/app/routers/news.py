from fastapi import APIRouter, HTTPException

from .. import storage
from ..models import NewsEvent, NewsEventsImportRequest, NewsRecord
from ..services import news_prompt

router = APIRouter(prefix="/customers", tags=["news"])


@router.get("/{customer_id}/news", response_model=NewsRecord)
def get_news(customer_id: str) -> NewsRecord:
    customer = storage.get_customer(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    record = storage.load_news_events(customer.domain)
    return record or NewsRecord(domain=customer.domain, events=[])


@router.get("/{customer_id}/news/prompt")
def get_news_prompt(customer_id: str) -> dict:
    customer = storage.get_customer(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    existing = storage.load_news_events(customer.domain)
    existing_headlines = [e.headline for e in existing.events] if existing else None
    prompt = news_prompt.build_prompt(customer.name, customer.domain, existing_headlines)
    return {"prompt": prompt}


@router.post("/{customer_id}/news/import", response_model=NewsRecord)
def import_news(customer_id: str, payload: NewsEventsImportRequest) -> NewsRecord:
    customer = storage.get_customer(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    if payload.events is not None:
        new_events = payload.events
    elif payload.text is not None:
        try:
            new_events = news_prompt.parse_import(payload.text)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    else:
        raise HTTPException(status_code=400, detail="Provide either 'text' or 'events'.")

    # News events accumulate over time (each import reports only genuinely new events,
    # per the prompt's instructions) rather than replacing the prior snapshot.
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
