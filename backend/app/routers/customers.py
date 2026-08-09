from fastapi import APIRouter, HTTPException

from .. import storage
from ..models import Customer, CustomerCreate, CustomerUpdate
from ..services import ssc_client

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=list[Customer])
def list_customers() -> list[Customer]:
    return storage.load_customers()


@router.post("", response_model=Customer, status_code=201)
def create_customer(payload: CustomerCreate) -> Customer:
    customer = storage.create_customer(payload)
    try:
        ssc_client.ensure_domain_in_portfolio(customer.domain)
    except Exception:
        pass  # score lookups will surface a clear error later if this domain is bad
    return customer


# Declared before /{customer_id} so "sync-from-portfolio" isn't matched as a customer id.
@router.post("/sync-from-portfolio")
def sync_from_portfolio() -> dict:
    """Pull in any company sitting in the shared SSC portfolio that isn't in our roster
    yet -- e.g. domains added directly through the SecurityScorecard UI."""
    try:
        entries = ssc_client.list_portfolio_companies()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not read the SSC portfolio: {exc}") from exc

    existing_domains = {c.domain.strip().lower() for c in storage.load_customers()}
    added: list[Customer] = []
    for entry in entries:
        domain = (entry.get("domain") or "").strip().lower()
        if not domain or domain in existing_domains:
            continue
        added.append(
            storage.create_customer(
                CustomerCreate(
                    name=entry.get("name") or domain,
                    domain=domain,
                    notes="Imported from the SecurityScorecard portfolio.",
                )
            )
        )
        existing_domains.add(domain)

    return {"added": [c.model_dump() for c in added], "added_count": len(added), "portfolio_size": len(entries)}


@router.get("/{customer_id}", response_model=Customer)
def get_customer(customer_id: str) -> Customer:
    customer = storage.get_customer(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.patch("/{customer_id}", response_model=Customer)
def update_customer(customer_id: str, payload: CustomerUpdate) -> Customer:
    customer = storage.update_customer(customer_id, payload)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.delete("/{customer_id}", status_code=204)
def delete_customer(customer_id: str) -> None:
    if not storage.delete_customer(customer_id):
        raise HTTPException(status_code=404, detail="Customer not found")
