from fastapi import APIRouter, HTTPException

from .. import storage
from ..models import ScoreSummary
from ..services import ssc_client

router = APIRouter(prefix="/customers", tags=["scores"])


@router.get("/{customer_id}/score", response_model=ScoreSummary)
def get_customer_score(customer_id: str) -> ScoreSummary:
    customer = storage.get_customer(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return ssc_client.build_score_summary(customer.domain)
