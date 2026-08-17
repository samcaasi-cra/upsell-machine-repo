from typing import Literal

from fastapi import APIRouter

from .. import storage
from ..models import AccountChip, NewsRecord, OpportunityBoardResponse
from ..services import signals
from ..services.aggregation import gather_all_customer_data
from ..services.concept_triggers import build_concept_cards
from ..services.mock_signals import build_mock_signal_cards
from ..services.opportunities import build_opportunity_cards, grade_sentiment

router = APIRouter(tags=["opportunities"])


def _build_industry_declines(entries) -> dict[str, list[tuple[str, int, str]]]:
    """industry -> [(customer_id, delta, window)] for tracked customers with a real
    score decline flag -- used to anonymously warn peers in the same industry (#11)."""
    declines: dict[str, list[tuple[str, int, str]]] = {}
    for customer, score, _, _ in entries:
        if not score.industry:
            continue
        delta, window = None, None
        if "score_down_10_182d" in score.flags and score.delta_182d:
            delta, window = score.delta_182d, "6 months"
        elif "score_down_5_30d" in score.flags and score.delta_30d:
            delta, window = score.delta_30d, "30 days"
        if delta is not None:
            declines.setdefault(score.industry, []).append((customer.id, delta, window))
    return declines


def _build_person_customer_map(entries) -> dict[str, list[tuple[str, str]]]:
    """identity (lowercased name, and linkedin_url when known) -> (customer name,
    last_purchase_product) for customers currently tracking that person -- used to
    detect an alumni move across our own customers (#19), and whether they're coming
    from a Titan MAX account (#8). Indexed under both keys since not every record has
    a LinkedIn URL captured, so a name-only record at one company must still match a
    LinkedIn-tagged record for the same person at another."""
    index: dict[str, list[tuple[str, str]]] = {}
    for customer, _, _, dm_record in entries:
        for p in dm_record.people:
            keys = {p.name.strip().lower()}
            if p.linkedin_url:
                keys.add(p.linkedin_url.strip().lower())
            for key in keys:
                index.setdefault(key, []).append((customer.name, customer.last_purchase_product or ""))
    return index


@router.get("/opportunities", response_model=OpportunityBoardResponse)
def get_opportunity_board(
    include_concepts: bool = False, audience: Literal["csm", "customer"] = "csm"
) -> OpportunityBoardResponse:
    """`include_concepts` adds illustrative cards for triggers from the brief that
    aren't built yet. Off by default so the honest view is the default.

    `audience="customer"` drops cards marked `csm_only` (pricing/discount info a
    customer shouldn't see) -- a demo stand-in for real account-permission gating."""
    entries = gather_all_customer_data()
    industry_stats_map = signals.industry_stats([(c.id, s.industry, s.current_score) for c, s, _, _ in entries])
    industry_declines = _build_industry_declines(entries)
    person_customer_map = _build_person_customer_map(entries)

    all_cards = []
    cards_by_customer: dict[str, int] = {}
    chips: list[AccountChip] = []
    for roster_index, (customer, score, usage, dm_record) in enumerate(entries):
        news_record = storage.load_news_events(customer.domain) or NewsRecord(domain=customer.domain, events=[])
        cards = build_opportunity_cards(
            customer,
            score,
            usage,
            dm_record,
            industry_stats_map,
            news_record,
            industry_declines,
            person_customer_map,
        )
        cards = cards + build_mock_signal_cards(customer, roster_index=roster_index)
        if include_concepts:
            cards = cards + build_concept_cards(
                customer, score, dm_record, roster_index=roster_index, roster_size=len(entries)
            )
        if audience == "customer":
            cards = [c for c in cards if not c.csm_only]
        all_cards.extend(cards)
        cards_by_customer[customer.id] = len(cards)
        chips.append(
            AccountChip(
                customer_id=customer.id,
                customer_name=customer.name,
                domain=customer.domain,
                industry=score.industry,
                score=score.current_score,
                grade=score.current_grade,
                sentiment=grade_sentiment(score.current_grade),
                open_opportunities=len(cards),
            )
        )

    chips.sort(key=lambda c: c.open_opportunities, reverse=True)
    return OpportunityBoardResponse(chips=chips, cards=all_cards)
