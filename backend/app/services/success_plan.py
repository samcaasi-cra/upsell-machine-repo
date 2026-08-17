"""Joint success plans: the agreement, and what has moved against it.

Two halves, deliberately kept distinct because their provenance is different:

  * The **plan** -- what problem the customer is solving, how many suppliers are in
    scope, the score both sides agreed to hit and by when. A CRM owns this. We have no
    Salesforce access, so it is mocked, seeded per customer so a demo is stable, and
    tagged data_source="mockup" everywhere it surfaces.

  * The **changes** -- everything that actually moved at this customer inside the
    review window. All real, from the same sources the board uses: live SSC score
    history and vendor detection, researched news and decision-makers, sample usage.

Keeping them apart matters: the plan is the thing we'd stop inventing the day
Salesforce is connected, and nothing else here would need to change.
"""

import random
from datetime import date, datetime, timedelta
from typing import Optional

from .. import storage
from ..models import (
    Customer,
    DecisionMakerRecord,
    ScoreSummary,
    SuccessPlan,
    SuccessPlanChange,
    SuccessPlanMetric,
    UsageSummary,
)
from . import mock_usage, ssc_client
from .opportunities import _dedupe_news_events, _is_ignored_vendor

WINDOW_DAYS = 30

# What a TPRM buyer is usually trying to fix. Picked per customer, not per render.
_OBJECTIVES = [
    "Reduce the risk of a breach reaching us through a supplier",
    "Cut the time it takes to spot a supplier problem, from months to days",
    "Prove to the board that third-party risk is falling, not just being tracked",
    "Get ahead of regulatory pressure on supply-chain oversight before the audit",
]


def _plan_rng(customer: Customer) -> random.Random:
    """Seeded per customer so the mocked plan is identical on every reload -- a demo
    where the agreed target moves each refresh is worse than no demo."""
    return random.Random(f"success-plan:{customer.id}")


def _straight_line_target(baseline: int, target: int, agreed: date, due: date, today: date) -> float:
    """Where the score should be today if progress were linear between the two dates."""
    total = (due - agreed).days
    if total <= 0:
        return float(target)
    elapsed = max(0, min((today - agreed).days, total))
    return baseline + (target - baseline) * (elapsed / total)


def _build_changes(
    customer: Customer,
    score: ScoreSummary,
    usage: UsageSummary,
    decision_makers: DecisionMakerRecord,
) -> list[SuccessPlanChange]:
    """Everything real that moved in the window, newest signal type first."""
    changes: list[SuccessPlanChange] = []
    today = date.today()
    cutoff = today - timedelta(days=WINDOW_DAYS)

    # --- the agreed metric itself (live) ---
    if score.delta_30d is not None and score.current_score is not None:
        d = score.delta_30d
        direction = "up" if d > 0 else "down" if d < 0 else "flat"
        if d == 0:
            headline = "Score unchanged"
            detail = f"Still {score.current_score}. No movement against the agreed target this period."
        else:
            headline = f"Score {'up' if d > 0 else 'down'} {abs(d)} point{'s' if abs(d) != 1 else ''}"
            detail = (
                f"Now {score.current_score}, from {score.current_score - d} thirty days ago. "
                f"{'Moving toward' if d > 0 else 'Moving away from'} the agreed target."
            )
        changes.append(
            SuccessPlanChange(
                category="Score",
                headline=headline,
                detail=detail,
                direction=direction,
                data_source="live",
                source_detail="SecurityScorecard score history API, 30-day delta.",
            )
        )

    # --- suppliers in scope (live) ---
    vendors = ssc_client.get_third_party_vendors(customer.domain, limit=50)
    at_risk = [
        v for v in vendors
        if isinstance(v.get("score"), int) and v["score"] < 50 and not _is_ignored_vendor(v.get("company"))
    ]
    if vendors:
        if at_risk:
            worst = min(at_risk, key=lambda v: v["score"])
            changes.append(
                SuccessPlanChange(
                    category="Suppliers",
                    headline=f"{len(at_risk)} supplier{'s' if len(at_risk) != 1 else ''} below 50",
                    detail=(
                        f"Worst is {worst.get('company') or worst.get('domain')} at {worst['score']}. "
                        f"Detected across {len(vendors)} third parties in their footprint."
                    ),
                    direction="down",
                    data_source="live",
                    source_detail="SecurityScorecard vendor-detection API; open-source projects filtered out.",
                )
            )
        else:
            changes.append(
                SuccessPlanChange(
                    category="Suppliers",
                    headline="No supplier below 50",
                    detail=f"All {len(vendors)} detected third parties are above the at-risk threshold.",
                    direction="up",
                    data_source="live",
                    source_detail="SecurityScorecard vendor-detection API.",
                )
            )

    # --- company events in the window (researched) ---
    news = storage.load_news_events(customer.domain)
    recent = []
    for event in _dedupe_news_events(news.events, customer.name) if news else []:
        try:
            if datetime.fromisoformat(event.date).date() >= cutoff:
                recent.append(event)
        except ValueError:
            continue
    for event in recent[:3]:
        changes.append(
            SuccessPlanChange(
                category="Company change",
                headline=event.headline,
                detail=event.summary,
                direction="up",
                data_source="researched",
                source_detail="Google News, extracted into structured events by the daily research agent.",
            )
        )

    # --- people (researched) ---
    new_people = [p for p in (decision_makers.people if decision_makers else []) if p.status == "new"]
    if new_people:
        who = ", ".join(f"{p.name} ({p.title})" for p in new_people[:2])
        changes.append(
            SuccessPlanChange(
                category="People",
                headline=f"{len(new_people)} new stakeholder{'s' if len(new_people) != 1 else ''}",
                detail=f"{who}. Not yet engaged against this plan.",
                direction="up",
                data_source="researched",
                source_detail="Decision-maker research, diffed against the previously cached list.",
            )
        )

    # --- engagement (sample) ---
    if usage.licensed_slots:
        pct = round(usage.slots_used / usage.licensed_slots * 100)
        changes.append(
            SuccessPlanChange(
                category="Engagement",
                headline=f"{pct}% of licensed slots in use",
                detail=(
                    f"{usage.slots_used} of {usage.licensed_slots} monitored, "
                    f"{usage.reports_generated_7d} reports generated in the last 7 days."
                ),
                direction="up" if usage.slots_delta_7d >= 0 else "down",
                data_source="sample",
                source_detail="Placeholder platform-usage generator until the real usage feed is connected.",
            )
        )

    return changes


def _summarise(customer: Customer, metric: SuccessPlanMetric, changes: list[SuccessPlanChange]) -> str:
    """A plain rollup of the window. Deterministic on purpose -- this is a status line
    a CSM reads before a QBR, so it should say the same thing twice in a row."""
    gap = metric.target - (metric.current if metric.current is not None else metric.baseline)
    lead = (
        f"{customer.name} is {'on track' if metric.on_track else 'behind'} against the agreed target: "
        f"{metric.current if metric.current is not None else '—'} today, {metric.target} by "
        f"{metric.due_date}"
    )
    lead += f" — {gap} point{'s' if abs(gap) != 1 else ''} to go." if gap > 0 else " — target met."

    if not changes:
        return lead + f" Nothing moved in the last {WINDOW_DAYS} days."

    down = [c for c in changes if c.direction == "down"]
    counts = f" {len(changes)} change{'s' if len(changes) != 1 else ''} in the last {WINDOW_DAYS} days"
    if down:
        return lead + counts + f", {len(down)} needing attention: {down[0].headline.lower()}."
    return lead + counts + ", none of them negative."


def build_plan(
    customer: Customer,
    score: ScoreSummary,
    usage: UsageSummary,
    decision_makers: DecisionMakerRecord,
) -> SuccessPlan:
    rng = _plan_rng(customer)
    today = date.today()

    high = rng.randrange(120, 260, 10)
    critical = rng.randrange(30, 80, 5)

    agreed = today - timedelta(days=rng.randint(60, 150))
    due = agreed + timedelta(days=rng.choice([180, 270, 365]))

    # Baseline is what their score ACTUALLY was on the day the plan was agreed, read
    # from live score history. Deriving it from today's score instead would bake in
    # improvement -- every account would sit comfortably ahead of plan, which is both
    # untrue and a useless demo. Falls back only when history doesn't reach that far.
    baseline = ssc_client._score_closest_to(
        [pt.model_dump() for pt in score.history],
        datetime.combine(agreed, datetime.min.time()),
    )
    if baseline is None:
        baseline = score.current_score - rng.randint(-4, 6) if score.current_score is not None else 70
    baseline = max(40, min(baseline, 95))
    target = min(baseline + rng.choice([5, 6, 7, 8]), 98)

    expected = _straight_line_target(baseline, target, agreed, due, today)
    current = score.current_score
    on_track = current is not None and current >= expected
    span = max(1, target - baseline)
    progress = 0 if current is None else round((current - baseline) / span * 100)
    progress = max(0, min(progress, 100))

    metric = SuccessPlanMetric(
        label="Average SecurityScorecard rating",
        baseline=baseline,
        current=current,
        target=target,
        due_date=due.isoformat(),
        on_track=on_track,
        progress_pct=progress,
    )

    changes = _build_changes(customer, score, usage, decision_makers)

    return SuccessPlan(
        customer_id=customer.id,
        customer_name=customer.name,
        domain=customer.domain,
        objective=rng.choice(_OBJECTIVES),
        scope=f"{high} high-risk and {critical} critical suppliers in scope",
        high_risk_suppliers=high,
        critical_suppliers=critical,
        metric=metric,
        owner=customer.csm or "Unassigned",
        sponsor=customer.sponsor or "Primary Contact",
        agreed_on=agreed.isoformat(),
        next_review=(today + timedelta(days=rng.randint(5, 40))).isoformat(),
        summary=_summarise(customer, metric, changes),
        changes=changes,
    )


def build_all() -> list[SuccessPlan]:
    plans = []
    for customer in storage.load_customers():
        score = ssc_client.build_score_summary(customer.domain)
        usage = mock_usage.build_usage_summary(customer.id)
        dm = storage.load_decision_makers(customer.domain) or DecisionMakerRecord(
            domain=customer.domain, people=[]
        )
        plans.append(build_plan(customer, score, usage, dm))
    return plans
