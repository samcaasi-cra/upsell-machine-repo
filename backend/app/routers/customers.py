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
