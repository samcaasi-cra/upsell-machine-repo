from fastapi import APIRouter, HTTPException

from .. import storage
from ..models import DecisionMakerImportRequest, DecisionMakerRecord
from ..services import decision_maker_prompt

router = APIRouter(prefix="/customers", tags=["decision-makers"])


@router.get("/{customer_id}/decision-makers", response_model=DecisionMakerRecord)
def get_decision_makers(customer_id: str) -> DecisionMakerRecord:
    customer = storage.get_customer(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    record = storage.load_decision_makers(customer.domain)
    return record or DecisionMakerRecord(domain=customer.domain, people=[])


@router.get("/{customer_id}/decision-makers/prompt")
def get_decision_maker_prompt(customer_id: str) -> dict:
    customer = storage.get_customer(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    existing = storage.load_decision_makers(customer.domain)
    existing_names = [p.name for p in existing.people] if existing else None
    prompt = decision_maker_prompt.build_prompt(customer.name, customer.domain, existing_names)
    return {"prompt": prompt}


@router.post("/{customer_id}/decision-makers/import", response_model=DecisionMakerRecord)
def import_decision_makers(customer_id: str, payload: DecisionMakerImportRequest) -> DecisionMakerRecord:
    customer = storage.get_customer(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    if payload.people is not None:
        people = payload.people
    elif payload.text:
        try:
            people = decision_maker_prompt.parse_import(payload.text)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    else:
        raise HTTPException(status_code=400, detail="Provide either 'text' or 'people'.")

    previous = storage.load_decision_makers(customer.domain)
    previous_names = {p.name.strip().lower() for p in previous.people} if previous else set()
    for person in people:
        person.status = "existing" if person.name.strip().lower() in previous_names else "new"

    return storage.save_decision_makers(customer.domain, people)
