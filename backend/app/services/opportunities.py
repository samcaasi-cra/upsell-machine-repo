"""Maps our real per-customer signals (live SSC score, mock usage, decision-maker
research) into the categorized "Opportunity Signals" cards from the Relationship
Growth Dashboard reference design: proof, adoption, expansion, engagement.

Deliberately only covers the triggers we have real (or already-established mock)
data for -- the same 7 signals already implemented in signals.py. No fabricated
supplier-portfolio, cost-savings, or news data. "Actioned" state is intentionally
not tracked here -- the frontend keeps it as session-only state, matching the
reference implementation.
"""

import hashlib
from datetime import date, datetime
from typing import Optional

from ..models import Customer, DecisionMakerRecord, NewsRecord, OpportunityCard, ScoreSummary, UsageSummary
from .signals import _ENGAGEMENT_THRESHOLD, _SLOT_CAPACITY_WARN_PCT

_BENCHMARK_VISITS_PER_USER = 5.0

_RECIPIENT_PREFERENCE = {
    "proof": ["Cyber Security"],
    "adoption": ["Cyber Security", "IT Services / Technology Controls"],
    "expansion": ["Risk / Governance / Compliance", "Third Party Risk Management"],
    "engagement": ["Cyber Security"],
}


def grade_sentiment(grade: Optional[str]) -> str:
    if grade in ("A", "B"):
        return "good"
    if grade == "C":
        return "info"
    if grade in ("D", "F"):
        return "watch"
    return "info"


def _pick_recipient(
    customer: Customer, decision_makers: Optional[DecisionMakerRecord], group: str
) -> tuple[str, str]:
    people = decision_makers.people if decision_makers else []
    for focus in _RECIPIENT_PREFERENCE.get(group, []):
        for p in people:
            if p.primary_focus == focus:
                return p.name, p.title
    if people:
        return people[0].name, people[0].title
    if customer.sponsor:
        return customer.sponsor, "Primary Contact"
    return "Primary Contact", "Primary Contact"


def _card_id(customer_id: str, group: str, label: str, description: str) -> str:
    raw = f"{customer_id}|{group}|{label}|{description}"
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def _signer(customer: Customer) -> str:
    return customer.csm or "The SecurityScorecard Customer Success Team"


def _make_card(
    group: str,
    customer: Customer,
    industry: Optional[str],
    value: str,
    label: str,
    sentiment: str,
    description: str,
    detected_at: str,
    subject: str,
    body_intro: str,
    decision_makers: Optional[DecisionMakerRecord],
    badge: Optional[str] = None,
    recipient: Optional[tuple[str, str]] = None,
) -> OpportunityCard:
    recipient_name, recipient_role = recipient or _pick_recipient(customer, decision_makers, group)
    first_name = recipient_name.split(" ")[0] if recipient_name != "Primary Contact" else "there"
    signer = _signer(customer)
    body = f"Hello {first_name},\n\n{body_intro}\n\nKind regards,\n{signer}\nSecurityScorecard Customer Success"
    return OpportunityCard(
        card_id=_card_id(customer.id, group, label, description),
        group=group,
        customer_id=customer.id,
        customer_name=customer.name,
        industry=industry,
        value=value,
        label=label,
        sentiment=sentiment,
        badge=badge,
        description=description,
        detected_at=detected_at,
        recipient_name=recipient_name,
        recipient_role=recipient_role,
        subject=subject,
        body=body,
    )


_NEWS_EVENT_META = {
    "acquisition": {
        "value": "M&A",
        "label": "acquisition",
        "subject_prefix": "Congratulations on the news",
        "advice": (
            "Acquisitions often bring new suppliers and systems into scope before due diligence is "
            "complete — worth extending monitoring coverage to the acquired company now, ahead of "
            "integration."
        ),
    },
    "new_office": {
        "value": "NEW",
        "label": "new office",
        "subject_prefix": "Congratulations on the expansion",
        "advice": (
            "New regional operations typically bring local suppliers that aren't yet in scope — worth "
            "adding the new entity and its suppliers to monitoring before it's fully operational."
        ),
    },
    "product_launch": {
        "value": "NEW",
        "label": "product launch",
        "subject_prefix": "Congratulations on the launch",
        "advice": (
            "New products usually bring a new supply chain with them — worth mapping the new product's "
            "suppliers into the monitored portfolio before the first customer security review."
        ),
    },
}


def build_opportunity_cards(
    customer: Customer,
    score: ScoreSummary,
    usage: UsageSummary,
    decision_makers: Optional[DecisionMakerRecord],
    industry_stats_map: dict[str, dict],
    news: Optional[NewsRecord] = None,
) -> list[OpportunityCard]:
    cards: list[OpportunityCard] = []
    today_iso = date.today().isoformat()

    def card(group, value, label, sentiment, description, subject, body_intro, detected_at=today_iso, **kw):
        cards.append(
            _make_card(
                group,
                customer,
                score.industry,
                value,
                label,
                sentiment,
                description,
                detected_at,
                subject,
                body_intro,
                decision_makers,
                **kw,
            )
        )

    # --- Proof of value ---
    if score.industry and score.industry in industry_stats_map:
        stats = industry_stats_map[score.industry]
        if stats["top_id"] == customer.id and score.current_score is not None:
            industry_label = score.industry.replace("_", " ")
            diff = round(score.current_score - stats["avg"])
            extra = f", {diff} points above the {round(stats['avg'])} average" if diff > 0 else ""
            card(
                "proof",
                "#1",
                f"in {industry_label}",
                "good",
                f"A score of {score.current_score} is the highest currently tracked among "
                f"{industry_label} peers{extra}.",
                f"{customer.name} now holds the top score in {industry_label}",
                f"At {score.current_score}, {customer.name} holds the highest SecurityScorecard rating we "
                f"currently track in {industry_label}{extra}. That's a differentiator worth using externally "
                "— consider featuring it on your customer-facing security page.",
            )

    score_up_delta, score_up_window = None, None
    if "score_up_5_30d" in score.flags and score.delta_30d:
        score_up_delta, score_up_window = score.delta_30d, "30 days"
    elif "score_up_10_182d" in score.flags and score.delta_182d:
        score_up_delta, score_up_window = score.delta_182d, "6 months"
    if score_up_delta and score.current_score is not None:
        card(
            "proof",
            f"+{score_up_delta}",
            f"SSC score → {score.current_score}",
            "good",
            f"SSC score rose {score_up_delta} points in the last {score_up_window} — "
            "strong renewal/ROI proof point.",
            f"Your SecurityScorecard rating moved up {score_up_delta} points",
            f"{customer.name}'s SecurityScorecard rating rose {score_up_delta} points in the last "
            f"{score_up_window}, now at {score.current_score}. Worth a short call to document what drove "
            "the improvement ahead of your next audit cycle.",
        )

    # --- Adoption signals ---
    if usage.licensed_slots > 0:
        pct = round(usage.slots_used / usage.licensed_slots * 100)
        if pct / 100 >= _SLOT_CAPACITY_WARN_PCT:
            card(
                "adoption",
                f"{pct}%",
                "vendor slots used",
                "watch",
                f"{usage.slots_used} of {usage.licensed_slots} licensed vendor slots are now in use "
                "— approaching the licensed ceiling.",
                f"{usage.slots_used} of {usage.licensed_slots} vendor slots now in use ({pct}%)",
                f"{customer.name} is now using {usage.slots_used} of {usage.licensed_slots} licensed vendor "
                f"slots ({pct}% utilisation). Worth a short conversation about headroom before you reach the "
                "ceiling, so onboarding a new supplier is never delayed by a licence limit.",
            )

    total_visits = sum(i.visits_7d for i in usage.individuals)
    engagement_score = usage.slots_filled_7d * 3 + usage.reports_generated_7d + total_visits
    if engagement_score >= _ENGAGEMENT_THRESHOLD and usage.individuals:
        avg_visits = total_visits / len(usage.individuals)
        multiplier = round(avg_visits / _BENCHMARK_VISITS_PER_USER, 1)
        card(
            "adoption",
            f"{multiplier}×",
            "logins per user",
            "good",
            f"{total_visits} logins this week across {len(usage.individuals)} active users "
            f"— {multiplier} per user, well above the platform benchmark.",
            "Your team is using the platform well above benchmark",
            f"{customer.name} logged {total_visits} platform logins this week across {len(usage.individuals)} "
            f"active users — {multiplier} per user, well above our usage benchmark of "
            f"{_BENCHMARK_VISITS_PER_USER:g}. That level of engagement usually means the team is ready for "
            "more advanced views.",
        )

    for name in usage.new_individuals[:3]:
        first = name.split(" ")[0]
        card(
            "adoption",
            "1st",
            f"login · {name}",
            "info",
            f"{name} logged in to SecurityScorecard for the first time.",
            f"Welcome to SecurityScorecard, {first}",
            f"You logged in to SecurityScorecard for the first time this week. Welcome aboard — you now have "
            f"visibility into {customer.name}'s own rating and its monitored data. Happy to walk you through "
            "the views that matter most for your role.",
            recipient=(name, "New user"),
        )

    # --- Expansion events (from news research: acquisitions, new offices, product launches) ---
    if news:
        for event in news.events[:5]:
            meta = _NEWS_EVENT_META[event.event_type]
            card(
                "expansion",
                meta["value"],
                meta["label"],
                "info",
                event.summary,
                f"{meta['subject_prefix']}: {event.headline}",
                f"{event.summary} {meta['advice']}",
                detected_at=event.date,
            )

    if decision_makers and decision_makers.people:
        detected_at = decision_makers.imported_at or today_iso
        try:
            detected_at = datetime.fromisoformat(detected_at).date().isoformat()
        except ValueError:
            detected_at = today_iso

        new_ciso = [p for p in decision_makers.people if p.status == "new" and p.is_ciso_or_biso]
        for p in new_ciso:
            role = "BISO" if "business information security" in p.title.lower() else "CISO"
            card(
                "expansion",
                "NEW",
                f"{role} appointed",
                "info",
                f"{p.name} was appointed {p.title}.",
                f"Congratulations on your appointment as {role}",
                f"Congratulations on your appointment as {role} at {customer.name}. Most incoming {role}s want "
                "a fast, honest read on where things stand — happy to offer a short handover briefing on the "
                "current scorecard and open risk items.",
                detected_at=detected_at,
                recipient=(p.name, p.title),
            )

        new_others = [p for p in decision_makers.people if p.status == "new" and not p.is_ciso_or_biso]
        if new_others:
            count = len(new_others)
            for p in new_others:
                card(
                    "engagement",
                    str(count),
                    "new stakeholders",
                    "good",
                    f"{p.name} ({p.title}) newly identified in the decision-making unit — not yet engaged.",
                    "Introducing your SecurityScorecard account team",
                    f"You're one of {count} new stakeholders identified in {customer.name}'s security "
                    "decision-making unit. Happy to offer a brief introduction so you have a direct line to "
                    "us alongside the rest of your team.",
                    detected_at=detected_at,
                    recipient=(p.name, p.title),
                )

    return cards
