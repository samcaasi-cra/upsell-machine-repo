from fastapi import APIRouter

from .. import storage
from ..models import AccountChip, NewsRecord, OpportunityBoardResponse
from ..services import signals
from ..services.aggregation import gather_all_customer_data
from ..services.opportunities import build_opportunity_cards, grade_sentiment

router = APIRouter(tags=["opportunities"])


@router.get("/opportunities", response_model=OpportunityBoardResponse)
def get_opportunity_board() -> OpportunityBoardResponse:
    entries = gather_all_customer_data()
    industry_stats_map = signals.industry_stats([(c.id, s.industry, s.current_score) for c, s, _, _ in entries])

    all_cards = []
    cards_by_customer: dict[str, int] = {}
    chips: list[AccountChip] = []
    for customer, score, usage, dm_record in entries:
        news_record = storage.load_news_events(customer.domain) or NewsRecord(domain=customer.domain, events=[])
        cards = build_opportunity_cards(customer, score, usage, dm_record, industry_stats_map, news_record)
        all_cards.extend(cards)
        cards_by_customer[customer.id] = len(cards)
        chips.append(
            AccountChip(
                customer_id=customer.id,
                customer_name=customer.name,
                industry=score.industry,
                score=score.current_score,
                grade=score.current_grade,
                sentiment=grade_sentiment(score.current_grade),
                open_opportunities=len(cards),
            )
        )

    chips.sort(key=lambda c: c.open_opportunities, reverse=True)
    return OpportunityBoardResponse(chips=chips, cards=all_cards)
