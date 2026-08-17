from typing import Optional

from ..models import Customer, DecisionMakerRecord, ScoreSummary, Signal, UsageSummary


def industry_top_ids(entries: list[tuple[str, Optional[str], Optional[int]]]) -> set[str]:
    """Given (customer_id, industry, current_score) tuples, return the customer_ids
    that hold the top score within their industry -- only for industries with at
    least 2 tracked customers, so a lone customer isn't trivially "top"."""
    return {stats["top_id"] for stats in industry_stats(entries).values()}


def industry_stats(entries: list[tuple[str, Optional[str], Optional[int]]]) -> dict[str, dict]:
    """Given (customer_id, industry, current_score) tuples, group by industry (only
    groups with >=2 tracked customers) and return {industry: {top_id, top_score, avg}}."""
    by_industry: dict[str, list[tuple[str, int]]] = {}
    for customer_id, industry, score in entries:
        if industry is None or score is None:
            continue
        by_industry.setdefault(industry, []).append((customer_id, score))

    stats: dict[str, dict] = {}
    for industry, members in by_industry.items():
        if len(members) < 2:
            continue
        best_id, best_score = max(members, key=lambda m: m[1])
        avg = sum(s for _, s in members) / len(members)
        stats[industry] = {"top_id": best_id, "top_score": best_score, "avg": avg}
    return stats

_SCORE_UPSELL_REASONS = {
    "score_up_5_30d": "SSC score up more than 5 points in the last 30 days",
    "score_up_10_182d": "SSC score up more than 10 points in the last 6 months",
    "score_above_95": "SSC score is above 95",
}
_SCORE_RISK_REASONS = {
    "score_down_5_30d": "SSC score down more than 5 points in the last 30 days",
    "score_down_10_182d": "SSC score down more than 10 points in the last 6 months",
}


_ENGAGEMENT_THRESHOLD = 75  # slots_filled_7d*3 + reports_generated_7d + total_visits_7d -- tuned so this
# only fires for genuinely high-engagement weeks (top ~quartile), not the typical case
_SLOT_CAPACITY_WARN_PCT = 0.85


def build_signal(
    customer: Customer,
    score: ScoreSummary,
    usage: UsageSummary,
    decision_makers: Optional[DecisionMakerRecord],
    top_in_industry: bool = False,
) -> Signal:
    upsell_reasons: list[str] = []
    risk_reasons: list[str] = []

    for flag in score.flags:
        if flag in _SCORE_UPSELL_REASONS:
            upsell_reasons.append(_SCORE_UPSELL_REASONS[flag])
        elif flag in _SCORE_RISK_REASONS:
            risk_reasons.append(_SCORE_RISK_REASONS[flag])

    if top_in_industry and score.industry:
        industry_label = score.industry.replace("_", " ")
        upsell_reasons.append(f"Top SSC score within its industry ({industry_label}) among tracked customers")

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

        engagement_score = usage.slots_filled_7d * 3 + usage.reports_generated_7d + total_visits
        if engagement_score >= _ENGAGEMENT_THRESHOLD:
            upsell_reasons.append("High platform engagement this week — route to CSM + Sales")

    if usage.licensed_slots > 0 and usage.slots_used / usage.licensed_slots >= _SLOT_CAPACITY_WARN_PCT:
        upsell_reasons.append(
            f"Nearing full utilisation of licensed vendor slots ({usage.slots_used}/{usage.licensed_slots} used)"
        )

    if usage.new_individuals:
        names = ", ".join(usage.new_individuals)
        upsell_reasons.append(f"New user(s) logged into SSC for the first time: {names}")

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
