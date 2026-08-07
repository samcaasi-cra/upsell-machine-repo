from fastapi import APIRouter, HTTPException

from .. import storage
from ..models import CustomerOverview, CustomerSummary, DecisionMakerRecord
from ..services import mock_usage, signals, ssc_client

router = APIRouter(tags=["upsell"])


@router.get("/signals", response_model=list[CustomerSummary])
def list_signals() -> list[CustomerSummary]:
    rows: list[CustomerSummary] = []
    for customer in storage.load_customers():
        score = ssc_client.build_score_summary(customer.domain)
        usage = mock_usage.build_usage_summary(customer.id)
        dm_record = storage.load_decision_makers(customer.domain) or DecisionMakerRecord(
            domain=customer.domain, people=[]
        )
        signal = signals.build_signal(customer, score, usage, dm_record)
        rows.append(
            CustomerSummary(
                customer=customer,
                current_score=score.current_score,
                current_grade=score.current_grade,
                score_error=score.error,
                delta_30d=score.delta_30d,
                usage=usage,
                decision_maker_count=len(dm_record.people),
                signal=signal,
            )
        )
    rows.sort(key=lambda r: r.signal.priority, reverse=True)
    return rows


@router.get("/customers/{customer_id}/overview", response_model=CustomerOverview)
def get_customer_overview(customer_id: str) -> CustomerOverview:
    customer = storage.get_customer(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    score = ssc_client.build_score_summary(customer.domain)
    usage = mock_usage.build_usage_summary(customer.id)
    dm_record = storage.load_decision_makers(customer.domain) or DecisionMakerRecord(
        domain=customer.domain, people=[]
    )
    signal = signals.build_signal(customer, score, usage, dm_record)

    return CustomerOverview(
        customer=customer,
        score=score,
        usage=usage,
        decision_makers=dm_record,
        signal=signal,
    )
