"""Which customers are ready for a SecurityScorecard partner product.

Not a new kind of signal. The signals that say a customer needs crisis-response help
are ones the board already detects -- a supplier in trouble, their own score sliding,
an acquisition, a new security leader. What this adds is the *recommendation*: given
those signals, which partner product is the right conversation, and why.

CSMs don't sell partner products because they have no time to work out who is ready.
This makes that list, with the reason printed next to each name so the CSM can judge
it rather than trust it.

Only Cytactic has rules today. EY and Grip are declared but marked upcoming, because
we don't yet know enough about what they sell to write honest rules for them.
"""

from datetime import date, datetime, timedelta
from typing import Optional

from ..models import Customer, DecisionMakerRecord, NewsRecord, ScoreSummary
from .aggregation import gather_all_customer_data
from .opportunities import _is_ignored_vendor
from . import ssc_client
from .. import storage

# A supplier at or below this score counts as being in trouble.
_SUPPLIER_AT_RISK = 50
# How far back a news event still counts as current.
_NEWS_WINDOW_DAYS = 45
# Score movement that counts as sliding.
_SCORE_DROP_30D = -5
_SCORE_DROP_182D = -10


PARTNERS = [
    {
        "id": "cytactic",
        "name": "Cytactic",
        "sells": "Crisis and incident-response readiness, including tabletop exercises",
        "status": "live",
    },
    {"id": "ey", "name": "EY", "sells": "", "status": "upcoming"},
    {"id": "grip", "name": "Grip", "sells": "", "status": "upcoming"},
]


def _recent(iso_date: str) -> bool:
    try:
        when = datetime.fromisoformat(iso_date).date()
    except (TypeError, ValueError):
        return False
    return when >= date.today() - timedelta(days=_NEWS_WINDOW_DAYS)


def _cytactic_reasons(
    customer: Customer,
    score: ScoreSummary,
    dm: DecisionMakerRecord,
    news: Optional[NewsRecord],
) -> list[dict]:
    """Each reason carries its own weight and provenance, so the view can show why an
    account is ranked where it is."""
    reasons: list[dict] = []

    # 1. A supplier in their footprint is in trouble -- the clearest trigger for
    #    rehearsing an incident that starts at a third party.
    try:
        vendors = ssc_client.get_third_party_vendors(customer.domain)
    except Exception:
        vendors = []
    at_risk = [
        v
        for v in vendors
        if not _is_ignored_vendor(v.get("company"))
        and isinstance(v.get("score"), int)
        and v["score"] <= _SUPPLIER_AT_RISK
    ]
    if at_risk:
        worst = min(at_risk, key=lambda v: v["score"])
        reasons.append(
            {
                "weight": 3,
                "text": f"{worst['company']} in their supply chain is scoring {worst['score']}",
                "source": "SecurityScorecard vendor-detection API",
                "tier": "live",
            }
        )

    # 2. Their own posture is sliding.
    if (score.delta_30d is not None and score.delta_30d <= _SCORE_DROP_30D) or (
        score.delta_182d is not None and score.delta_182d <= _SCORE_DROP_182D
    ):
        drop = score.delta_30d if (score.delta_30d or 0) <= _SCORE_DROP_30D else score.delta_182d
        window = "30 days" if (score.delta_30d or 0) <= _SCORE_DROP_30D else "6 months"
        reasons.append(
            {
                "weight": 2,
                "text": f"Their own score is down {abs(drop)} points over {window}",
                "source": "SecurityScorecard score history",
                "tier": "live",
            }
        )

    # 3. An acquisition brings a new estate to defend, and a crisis plan that no longer
    #    covers it.
    for event in (news.events if news else []):
        if event.event_type == "acquisition" and _recent(event.date):
            reasons.append(
                {
                    "weight": 2,
                    "text": f"Acquisition in the last {_NEWS_WINDOW_DAYS} days: {event.headline}",
                    "source": "News research",
                    "tier": "researched",
                }
            )
            break

    # 4. A new security leader typically reviews incident readiness early.
    new_leaders = [p for p in dm.people if p.status == "new" and p.is_ciso_or_biso]
    if new_leaders:
        reasons.append(
            {
                "weight": 2,
                "text": f"New security leader identified: {new_leaders[0].title}",
                "source": "Decision-maker research",
                "tier": "researched",
            }
        )

    return reasons


def build_partner_fit() -> dict:
    """Every customer scored for partner fit, best first."""
    rows = []
    for customer, score, _usage, dm in gather_all_customer_data():
        news = storage.load_news_events(customer.domain)
        reasons = _cytactic_reasons(customer, score, dm, news)
        if not reasons:
            continue
        rows.append(
            {
                "customer_id": customer.id,
                "customer_name": customer.name,
                "domain": customer.domain,
                "partner_id": "cytactic",
                "fit_score": sum(r["weight"] for r in reasons),
                "reasons": reasons,
                "recipient_role": customer.sponsor or "Primary Contact",
                "talk_track": (
                    "Open on what their own data shows, not on the product: the supplier or score "
                    "movement above. Then offer a tabletop exercise that rehearses exactly that "
                    "scenario, run by Cytactic."
                ),
            }
        )

    rows.sort(key=lambda r: (-r["fit_score"], r["customer_name"]))
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "partners": PARTNERS,
        "rules": [
            "A supplier in their footprint is scoring 50 or below (weight 3)",
            "Their own score has fallen 5+ points in 30 days, or 10+ in 6 months (weight 2)",
            f"An acquisition in the last {_NEWS_WINDOW_DAYS} days (weight 2)",
            "A new CISO or BISO has been identified (weight 2)",
        ],
        "rows": rows,
    }
