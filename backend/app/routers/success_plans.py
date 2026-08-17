from fastapi import APIRouter, HTTPException

from ..models import SuccessPlan
from ..services import success_plan

router = APIRouter(tags=["success-plans"])


@router.get("/success-plans")
def list_success_plans() -> list[SuccessPlan]:
    """A joint success plan per customer: the agreement, and what has moved against it."""
    return success_plan.build_all()


@router.get("/customers/{customer_id}/success-plan")
def get_success_plan(customer_id: str) -> SuccessPlan:
    for plan in success_plan.build_all():
        if plan.customer_id == customer_id:
            return plan
    raise HTTPException(status_code=404, detail=f"No customer with id {customer_id}")
