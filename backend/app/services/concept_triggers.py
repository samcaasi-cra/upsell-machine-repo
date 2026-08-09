"""Illustrative cards for the triggers from the brief that aren't built yet.

These exist so the full 23-trigger product vision can be shown in a demo. They are
NOT real signals -- every number here is invented, and each card is tagged
data_source="concept" plus the trigger number it illustrates, so it renders with a
distinct treatment and can never be mistaken for live data.

They are excluded from /opportunities by default. The caller has to ask for them
explicitly (?include_concepts=true), so the honest view is the one you get without
thinking about it.

Each entry names the real data source it's waiting on -- that's the point of showing
them: "here's the card, here's what we'd need to connect to make it real."
"""

import hashlib
import random
from datetime import date, timedelta
from typing import Optional

from ..models import Customer, DecisionMakerRecord, OpportunityCard, RecipientOption, ScoreSummary


def _card_id(customer_id: str, trigger: str) -> str:
    return "concept-" + hashlib.sha1(f"{customer_id}|{trigger}".encode()).hexdigest()[:12]


def _recipient(customer: Customer, decision_makers: Optional[DecisionMakerRecord]) -> tuple[str, str]:
    people = decision_makers.people if decision_makers else []
    if people:
        return people[0].name, people[0].title
    if customer.sponsor:
        return customer.sponsor, "Sponsor"
    return "Primary Contact", "Primary Contact"


def build_concept_cards(
    customer: Customer,
    score: ScoreSummary,
    decision_makers: Optional[DecisionMakerRecord],
    roster_index: int = 0,
    roster_size: int = 1,
) -> list[OpportunityCard]:
    """Deterministic per customer, so a demo shows the same numbers every time.

    Triggers are spread across the roster rather than stamped onto every account:
    putting all nine on all thirteen customers would bury the real signals and look
    nothing like reality, where a given account has one or two things happening.
    """
    rng = random.Random(f"concept:{customer.id}")
    today = date.today()
    industry_label = (score.industry or "your sector").replace("_", " ")
    recipient_name, recipient_role = _recipient(customer, decision_makers)
    first = recipient_name.split(" ")[0] if recipient_name != "Primary Contact" else "there"
    signer = customer.csm or "The SecurityScorecard Customer Success Team"

    saving = rng.randint(3, 14) * 10_000
    incidents = rng.randint(6, 28)
    hr_before = rng.randint(7, 14)
    hr_after = hr_before - rng.randint(2, 5)
    pf_before = rng.randint(64, 78)
    pf_gain = rng.randint(5, 12)
    added = rng.randint(4, 15)
    lead_days = rng.randint(11, 46)
    share_pct = rng.randint(4, 19)
    review_days = rng.randint(3, 21)
    quarter = rng.choice(["Q1 2027", "Q2 2027", "Q4 2026"])
    supplier = rng.choice(["Kestrel Freight", "Dunmore Systems", "Ashgrove Partners", "Halden Logistics"])

    # (trigger, group, value, label, sentiment, description, subject, body_intro, needs, days_ago)
    specs = [
        (
            "#9", "proof", f"£{saving // 1000}k", "avoided costs YTD", "good",
            f"£{saving:,} in avoided remediation and audit costs this year, across {incidents} incidents "
            "caught before they escalated.",
            f"£{saving:,} in avoided costs this year",
            f"{customer.name} has avoided roughly £{saving:,} in remediation and audit costs this year, "
            f"across {incidents} incidents caught early. Worth documenting ahead of renewal in a form "
            "finance can use.",
            "An agreed ROI / avoided-incident model", 6,
        ),
        (
            "#14", "proof", f"{hr_before}→{hr_after}", "high-risk suppliers", "good",
            f"High-risk suppliers in the monitored portfolio fell from {hr_before} to {hr_after} after the "
            "latest remediation push.",
            f"High-risk suppliers down from {hr_before} to {hr_after}",
            f"High-risk suppliers in {customer.name}'s monitored portfolio fell from {hr_before} to "
            f"{hr_after} this period. Worth reviewing what changed and applying the same playbook to the "
            "remainder.",
            "Per-customer supplier portfolios in SSC", 7,
        ),
        (
            "#15", "proof", f"+{pf_gain}", f"portfolio avg → {pf_before + pf_gain}", "good",
            f"Supplier portfolio average rose from {pf_before} to {pf_before + pf_gain} this quarter.",
            f"Your supplier portfolio average climbed {pf_gain} points",
            f"{customer.name}'s monitored supplier portfolio average rose from {pf_before} to "
            f"{pf_before + pf_gain} this quarter — a strong data point for your next board conversation.",
            "Per-customer supplier portfolios in SSC", 13,
        ),
        (
            "#8", "proof", f"{lead_days}d", "ahead of disclosure", "good",
            f"{supplier} was flagged high-risk {lead_days} days before its breach was publicly disclosed.",
            f"We flagged {supplier} {lead_days} days before disclosure",
            f"SecurityScorecard flagged {supplier} as high-risk {lead_days} days before the breach became "
            "public. That lead time is worth citing next time the board asks what third-party monitoring "
            "is buying you.",
            "A breach-event feed to join against score history", 9,
        ),
        (
            "#4", "expansion", "REG", "new industry rule", "info",
            f"A finalised third-party risk rule for {industry_label} takes effect {quarter}.",
            f"New third-party risk rule affecting {industry_label.title()}",
            f"A third-party risk rule affecting {industry_label} was finalised recently and takes effect "
            f"{quarter}. Worth a gap check of {customer.name}'s current supplier monitoring well ahead of "
            "the date.",
            "A regulatory tracking feed", 3,
        ),
        (
            "#16", "expansion", f"+{share_pct}%", "share price vs peers", "info",
            f"Share price is up {share_pct}% against {industry_label} peers this quarter — often a sign of "
            "budget headroom.",
            "Congratulations on a strong quarter",
            f"{customer.name}'s share price is up {share_pct}% against {industry_label} peers this quarter. "
            "Often a good moment to revisit coverage that was deferred on budget grounds.",
            "A stock market data API", 5,
        ),
        (
            "#18", "engagement", "★", "forum compliment", "good",
            f"A {customer.name} user posted positive feedback about the platform in the Customer Forum.",
            "Thank you for the kind words",
            f"Someone from {customer.name} left positive feedback in the Customer Forum. Worth thanking "
            "them, and asking whether they'd be open to a short reference conversation.",
            "Access to the Customer Forum tool", 4,
        ),
        (
            "#20", "engagement", "POST", "DMU posted on cyber", "info",
            f"{recipient_name} posted publicly about third-party risk this week.",
            "Enjoyed your post on third-party risk",
            f"Saw your recent post on third-party risk — it lines up closely with what we're seeing across "
            "the portfolio. Happy to compare notes if useful.",
            "Social listening (LinkedIn API is partner-gated)", 2,
        ),
        (
            "#23", "engagement", f"{review_days}d", "until CSM review", "info",
            f"Quarterly CSM review due in {review_days} days"
            + (f", owned by {customer.csm}." if customer.csm else " — no CSM assigned yet."),
            f"Confirming our upcoming review",
            f"Our next review for {customer.name} is about {review_days} days out. Worth confirming "
            "attendees this week so the agenda matches what matters to you right now.",
            "Salesforce / calendar integration", -review_days,
        ),
    ]

    options = [RecipientOption(name=recipient_name, role=recipient_role)]
    for p in decision_makers.people if decision_makers else []:
        if p.name != recipient_name:
            options.append(RecipientOption(name=p.name, role=p.title))

    # One trigger per account, cycling through the list, so all nine appear somewhere
    # across the roster without any single account carrying an implausible pile of them.
    selected = [specs[roster_index % len(specs)]] if roster_size > 1 else specs

    cards: list[OpportunityCard] = []
    for trigger, group, value, label, sentiment, description, subject, body_intro, needs, days_ago in selected:
        cards.append(
            OpportunityCard(
                card_id=_card_id(customer.id, trigger),
                group=group,
                customer_id=customer.id,
                customer_name=customer.name,
                industry=score.industry,
                value=value,
                label=label,
                sentiment=sentiment,
                data_source="concept",
                concept_trigger=f"{trigger} · needs {needs}",
                description=description,
                detected_at=(today - timedelta(days=days_ago)).isoformat(),
                recipient_name=recipient_name,
                recipient_role=recipient_role,
                recipient_options=options,
                subject=subject,
                body=(
                    f"Hello {first},\n\n{body_intro}\n\nKind regards,\n{signer}\n"
                    "SecurityScorecard Customer Success"
                ),
            )
        )
    return cards
