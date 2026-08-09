from fastapi import APIRouter, HTTPException

from .. import storage
from ..models import Customer, DecisionMaker, DecisionMakerImportRequest, DecisionMakerRecord
from ..services import decision_maker_prompt, web_research

router = APIRouter(prefix="/customers", tags=["decision-makers"])


def _require_customer(customer_id: str) -> Customer:
    customer = storage.get_customer(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


def _mark_new_and_save(customer: Customer, people: list[DecisionMaker]) -> DecisionMakerRecord:
    previous = storage.load_decision_makers(customer.domain)
    previous_names = {p.name.strip().lower() for p in previous.people} if previous else set()
    for person in people:
        person.status = "existing" if person.name.strip().lower() in previous_names else "new"
    return storage.save_decision_makers(customer.domain, people)


@router.get("/{customer_id}/decision-makers", response_model=DecisionMakerRecord)
def get_decision_makers(customer_id: str) -> DecisionMakerRecord:
    customer = _require_customer(customer_id)
    record = storage.load_decision_makers(customer.domain)
    return record or DecisionMakerRecord(domain=customer.domain, people=[])


@router.get("/{customer_id}/decision-makers/prompt")
def get_decision_maker_prompt(customer_id: str) -> dict:
    customer = _require_customer(customer_id)
    existing = storage.load_decision_makers(customer.domain)
    existing_names = [p.name for p in existing.people] if existing else None
    prompt = decision_maker_prompt.build_prompt(customer.name, customer.domain, existing_names)
    return {"prompt": prompt}


@router.post("/{customer_id}/decision-makers/import", response_model=DecisionMakerRecord)
def import_decision_makers(customer_id: str, payload: DecisionMakerImportRequest) -> DecisionMakerRecord:
    customer = _require_customer(customer_id)

    if payload.people is not None:
        people = payload.people
    elif payload.text:
        try:
            people = decision_maker_prompt.parse_import(payload.text)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    else:
        raise HTTPException(status_code=400, detail="Provide either 'text' or 'people'.")

    return _mark_new_and_save(customer, people)


@router.post("/{customer_id}/decision-makers/auto-research", response_model=DecisionMakerRecord)
def auto_research_decision_makers(customer_id: str) -> DecisionMakerRecord:
    """Automated alternative to the copy/paste flow: searches and scrapes the web, then
    has OpenAI extract the same JSON shape the manual flow produces."""
    customer = _require_customer(customer_id)
    if not web_research.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Auto-research needs an OPENAI_API_KEY in backend/.env. Use the copy/paste flow instead.",
        )

    existing = storage.load_decision_makers(customer.domain)
    existing_names = [p.name for p in existing.people] if existing else None
    prompt = decision_maker_prompt.build_prompt(customer.name, customer.domain, existing_names)

    queries = [
        f"{customer.name} CISO OR \"Chief Information Security Officer\" linkedin",
        f"{customer.name} \"head of information security\" OR \"head of cyber security\" linkedin",
        f"{customer.name} \"third party risk\" OR \"vendor risk\" OR compliance officer linkedin",
    ]
    try:
        # People move less often than news breaks -- search a wider window. Skip the
        # news feed here: finding who holds a role is a profile lookup, not a headline.
        raw = web_research.research_to_json(prompt, queries, recency="y", include_news=False)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Auto-research failed: {exc}") from exc

    if raw is None:
        return existing or DecisionMakerRecord(domain=customer.domain, people=[])

    try:
        people = decision_maker_prompt.parse_import(raw)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=f"Could not parse the research result: {exc}") from exc

    return _mark_new_and_save(customer, people)
