from fastapi import APIRouter, HTTPException

from .. import storage
from ..models import Customer, CustomerOverview, CustomerSummary, DecisionMakerRecord, ScoreSummary, UsageSummary
from ..services import mock_usage, signals, ssc_client

router = APIRouter(tags=["upsell"])


def _gather_all() -> list[tuple[Customer, ScoreSummary, UsageSummary, DecisionMakerRecord]]:
    rows = []
    for customer in storage.load_customers():
        score = ssc_client.build_score_summary(customer.domain)
        usage = mock_usage.build_usage_summary(customer.id)
        dm_record = storage.load_decision_makers(customer.domain) or DecisionMakerRecord(
            domain=customer.domain, people=[]
        )
        rows.append((customer, score, usage, dm_record))
    return rows


@router.get("/signals", response_model=list[CustomerSummary])
def list_signals() -> list[CustomerSummary]:
    entries = _gather_all()
    top_ids = signals.industry_top_ids([(c.id, s.industry, s.current_score) for c, s, _, _ in entries])

    rows: list[CustomerSummary] = []
    for customer, score, usage, dm_record in entries:
        signal = signals.build_signal(customer, score, usage, dm_record, top_in_industry=customer.id in top_ids)
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
    entries = _gather_all()
    top_ids = signals.industry_top_ids([(c.id, s.industry, s.current_score) for c, s, _, _ in entries])

    match = next((e for e in entries if e[0].id == customer_id), None)
    if match is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    customer, score, usage, dm_record = match

    signal = signals.build_signal(customer, score, usage, dm_record, top_in_industry=customer.id in top_ids)

    return CustomerOverview(
        customer=customer,
        score=score,
        usage=usage,
        decision_makers=dm_record,
        signal=signal,
    )
