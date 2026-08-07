from fastapi import APIRouter, HTTPException

from .. import storage
from ..models import UsageSummary
from ..services import mock_usage

router = APIRouter(prefix="/customers", tags=["usage"])


@router.get("/{customer_id}/usage", response_model=UsageSummary)
def get_customer_usage(customer_id: str) -> UsageSummary:
    customer = storage.get_customer(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return mock_usage.build_usage_summary(customer.id)
