from fastapi import APIRouter, HTTPException

from .. import storage
from ..models import CustomerOverview, CustomerSummary, NewsRecord
from ..services import signals
from ..services.aggregation import gather_all_customer_data

router = APIRouter(tags=["upsell"])


@router.get("/signals", response_model=list[CustomerSummary])
def list_signals() -> list[CustomerSummary]:
    entries = gather_all_customer_data()
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
    entries = gather_all_customer_data()
    top_ids = signals.industry_top_ids([(c.id, s.industry, s.current_score) for c, s, _, _ in entries])

    match = next((e for e in entries if e[0].id == customer_id), None)
    if match is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    customer, score, usage, dm_record = match

    signal = signals.build_signal(customer, score, usage, dm_record, top_in_industry=customer.id in top_ids)
    news_record = storage.load_news_events(customer.domain) or NewsRecord(domain=customer.domain, events=[])

    return CustomerOverview(
        customer=customer,
        score=score,
        usage=usage,
        decision_makers=dm_record,
        news=news_record,
        signal=signal,
    )
