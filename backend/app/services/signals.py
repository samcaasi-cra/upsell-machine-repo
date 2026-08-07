from typing import Optional

from ..models import Customer, DecisionMakerRecord, ScoreSummary, Signal, UsageSummary

_SCORE_UPSELL_REASONS = {
    "score_up_5_30d": "SSC score up more than 5 points in the last 30 days",
    "score_up_10_182d": "SSC score up more than 10 points in the last 6 months",
    "score_above_95": "SSC score is above 95",
}
_SCORE_RISK_REASONS = {
    "score_down_5_30d": "SSC score down more than 5 points in the last 30 days",
    "score_down_10_182d": "SSC score down more than 10 points in the last 6 months",
}


def build_signal(
    customer: Customer,
    score: ScoreSummary,
    usage: UsageSummary,
    decision_makers: Optional[DecisionMakerRecord],
) -> Signal:
    upsell_reasons: list[str] = []
    risk_reasons: list[str] = []

    for flag in score.flags:
        if flag in _SCORE_UPSELL_REASONS:
            upsell_reasons.append(_SCORE_UPSELL_REASONS[flag])
        elif flag in _SCORE_RISK_REASONS:
            risk_reasons.append(_SCORE_RISK_REASONS[flag])

    total_visits = sum(i.visits_7d for i in usage.individuals)
    if usage.slots_filled_7d == 0 and usage.reports_generated_7d == 0 and total_visits == 0:
        risk_reasons.append("No platform activity (slots, reports, or logins) in the last 7 days")
    else:
        if usage.slots_delta_7d > 0:
            upsell_reasons.append(f"Slots filled trending up (+{usage.slots_delta_7d} vs. prior week)")
        elif usage.slots_delta_7d < -2:
            risk_reasons.append(f"Slots filled dropping ({usage.slots_delta_7d} vs. prior week)")
        if usage.reports_delta_7d > 3:
            upsell_reasons.append(f"Reports generated trending up (+{usage.reports_delta_7d} vs. prior week)")
        elif usage.reports_delta_7d < -3:
            risk_reasons.append(f"Reports generated dropping ({usage.reports_delta_7d} vs. prior week)")

    if decision_makers and decision_makers.people:
        new_ciso = [p for p in decision_makers.people if p.status == "new" and p.is_ciso_or_biso]
        new_others = [p for p in decision_makers.people if p.status == "new" and not p.is_ciso_or_biso]
        for p in new_ciso:
            upsell_reasons.append(f"New CISO/BISO identified: {p.name} ({p.title})")
        for p in new_others:
            upsell_reasons.append(f"New decision-maker identified: {p.name} ({p.title})")

        if customer.sponsor:
            sponsor_lower = customer.sponsor.strip().lower()
            still_present = any(sponsor_lower in p.name.strip().lower() for p in decision_makers.people)
            if not still_present:
                risk_reasons.append(
                    f"Sponsor '{customer.sponsor}' no longer appears among identified decision-makers"
                )

    if not customer.csm:
        risk_reasons.append("No CSM currently assigned")

    if risk_reasons:
        level = "retention_risk"
    elif upsell_reasons:
        level = "upsell"
    else:
        level = "neutral"

    priority = len(risk_reasons) * 10 + len(upsell_reasons) * 5

    return Signal(
        customer_id=customer.id,
        level=level,
        priority=priority,
        reasons=risk_reasons + upsell_reasons,
    )
