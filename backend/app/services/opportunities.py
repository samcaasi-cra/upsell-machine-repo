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
import re
from datetime import date, datetime
from typing import Optional

from ..models import (
    Customer,
    DecisionMakerRecord,
    NewsRecord,
    OpportunityCard,
    RecipientOption,
    ScoreSummary,
    UsageSummary,
)
from .. import config
from . import ssc_client
from .signals import _ENGAGEMENT_THRESHOLD, _SLOT_CAPACITY_WARN_PCT

_BENCHMARK_VISITS_PER_USER = 5.0
_SUPPLIER_RISK_SCORE_THRESHOLD = 50  # roughly grade F territory -- deliberately strict,
# see _NOT_REAL_VENDORS below for why a looser bar is too noisy to be a signal
_QUESTIONNAIRE_LOW_REMAINING_PCT = 0.20  # warn once 80%+ of the licensed questionnaires are used

# vendor-detection frequently flags open-source/infrastructure projects that every
# company's tech stack touches (detected via fingerprinting, e.g. "runs on Apache") --
# these aren't real third-party business relationships and score chronically low,
# so without this filter this trigger fires for almost every customer.
_NOT_REAL_VENDORS = {
    "apache", "apache software foundation", "django", "linux foundation",
    "the linux foundation", "cncf", "nginx", "openssl", "w3c", "python software foundation",
}

_NEWS_NOISE_WORDS = {
    "the", "and", "for", "with", "from", "that", "this", "into", "its", "has", "have",
    "will", "new", "announced", "announces", "company", "million", "billion", "reports",
}


def _news_subjects(event, customer_name: str) -> set[str]:
    """The distinctive named things an event is about -- the other company in a deal,
    the product, the city. Capitalised words carry that, minus the customer's own name
    (present in nearly every headline) and generic filler.
    """
    own = {w.lower() for w in re.findall(r"[A-Za-z0-9]+", customer_name)}
    words = re.findall(r"\b[A-Z][A-Za-z0-9&.\-]{2,}", f"{event.headline} {event.summary}")
    return {w.lower().strip(".") for w in words} - own - _NEWS_NOISE_WORDS


def _dedupe_news_events(events, customer_name: str) -> list:
    """Collapse several articles covering one event down to a single card.

    Google News returns each story from multiple outlets, so an acquisition shows up
    two or three times with different wording ("a $53bn takeover offer" vs "a cash
    offer of $60.50 per share"). Text similarity is too blunt to catch that, but the
    named subject isn't: same event type plus a shared distinctive name means the same
    story. Distinct deals for one customer keep their own cards.
    """
    kept: list = []
    kept_subjects: list[set[str]] = []
    for event in events:
        subjects = _news_subjects(event, customer_name)
        duplicate = False
        for i, existing in enumerate(kept):
            if existing.event_type == event.event_type and subjects & kept_subjects[i]:
                duplicate = True
                break
        if not duplicate:
            kept.append(event)
            kept_subjects.append(subjects)
    return kept


def _is_ignored_vendor(name: Optional[str]) -> bool:
    """Vendor detection returns names with legal suffixes attached ("Python Software
    Foundation Corp"), so comparing the whole string against _NOT_REAL_VENDORS misses
    them. Match on the leading words instead, requiring a word boundary after the term
    so a short entry like "nginx" can't swallow an unrelated "Nginxy Ltd".
    """
    cleaned = re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).strip()
    # "The Apache Software Foundation" and "Apache Software Foundation" are the same body.
    cleaned = re.sub(r"^the ", "", cleaned)
    if not cleaned:
        return False
    return any(cleaned == term or cleaned.startswith(term + " ") for term in _NOT_REAL_VENDORS)


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


def _card_id(customer_id: str, group: str, label: str, description: str, *extra: str) -> str:
    # `description` is now a short, often-templated instruction shared across similar
    # events (e.g. every "new stakeholder" card reads the same), so on its own it no
    # longer guarantees a unique id -- callers pass distinguishing extras (detail text,
    # recipient, detected_at) to keep multiple same-type cards for one customer distinct.
    raw = "|".join([customer_id, group, label, description, *extra])
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def _signer(customer: Customer) -> str:
    return customer.csm or config.CSM_NAME


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
    data_source: str = "live",
    detail: Optional[str] = None,
    source_url: Optional[str] = None,
    source_detail: Optional[str] = None,
    csm_only: bool = False,
) -> OpportunityCard:
    recipient_name, recipient_role = recipient or _pick_recipient(customer, decision_makers, group)
    first_name = recipient_name.split(" ")[0] if recipient_name != "Primary Contact" else "there"

    options: list[RecipientOption] = []
    seen_names = set()
    for candidate_name, candidate_role in [(recipient_name, recipient_role)] + [
        (p.name, p.title) for p in (decision_makers.people if decision_makers else [])
    ]:
        key = candidate_name.strip().lower()
        if key and key not in seen_names:
            seen_names.add(key)
            options.append(RecipientOption(name=candidate_name, role=candidate_role))
    if customer.sponsor and customer.sponsor.strip().lower() not in seen_names:
        options.append(RecipientOption(name=customer.sponsor, role="Sponsor"))

    signer = _signer(customer)
    # Congratulating someone on their own news reads better with the article attached --
    # it shows you actually read it rather than reacting to an alert.
    reference = f"\n\nFor reference: {source_url}" if source_url else ""
    body = (
        f"Hello {first_name},\n\n{body_intro}{reference}"
        f"\n\nKind regards,\n{signer}\nSecurityScorecard Customer Success"
    )
    return OpportunityCard(
        card_id=_card_id(customer.id, group, label, description, detail or "", recipient_name, detected_at),
        group=group,
        customer_id=customer.id,
        customer_name=customer.name,
        industry=industry,
        value=value,
        label=label,
        sentiment=sentiment,
        data_source=data_source,
        badge=badge,
        description=description,
        detail=detail,
        detected_at=detected_at,
        recipient_name=recipient_name,
        recipient_role=recipient_role,
        recipient_options=options,
        subject=subject,
        body=body,
        source_url=source_url,
        source_detail=source_detail,
        csm_only=csm_only,
    )


_NEWS_EVENT_META = {
    "acquisition": {
        "value": "M&A",
        "label": "acquisition",
        "cta": "Congratulate them and offer to extend coverage to the acquisition.",
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
        "cta": "Congratulate them and offer to cover the new office's suppliers.",
        "subject_prefix": "Congratulations on the expansion",
        "advice": (
            "New regional operations typically bring local suppliers that aren't yet in scope — worth "
            "adding the new entity and its suppliers to monitoring before it's fully operational."
        ),
    },
    "product_launch": {
        "value": "NEW",
        "label": "product launch",
        "cta": "Congratulate them and offer to map the new product's suppliers.",
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
    industry_declines: Optional[dict[str, list[tuple[str, int, str]]]] = None,
    person_customer_map: Optional[dict[str, list[str]]] = None,
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
                "vs peers",
                "good",
                f"Tell {customer.name} executives that they scored highest amongst "
                "their specific peers on security.",
                f"{customer.name} now holds the top score in {industry_label}",
                f"At {score.current_score}, {customer.name} holds the highest SecurityScorecard rating we "
                f"currently track in {industry_label}{extra}. That's a differentiator worth using externally "
                "— consider featuring it on your customer-facing security page.",
                detail=f"A score of {score.current_score} is the highest currently tracked among "
                f"{industry_label} peers{extra}.",
                source_detail="SecurityScorecard API — GET /companies/{domain} for the current score, "
                "compared across every tracked customer sharing this industry field. "
                "backend/app/services/ssc_client.py:106 (get_company()); "
                "backend/app/services/signals.py:13 (industry_stats()).",
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
            f"Cite the {score_up_delta}-point gain as renewal proof.",
            f"Your SecurityScorecard rating moved up {score_up_delta} points",
            f"{customer.name}'s SecurityScorecard rating rose {score_up_delta} points in the last "
            f"{score_up_window}, now at {score.current_score}. Worth a short call to document what drove "
            "the improvement ahead of your next audit cycle.",
            detail=f"SSC score rose {score_up_delta} points in the last {score_up_window} — "
            "strong renewal/ROI proof point.",
            source_detail="SecurityScorecard API — GET /companies/{domain}/history/score, timing=weekly, "
            "feeding the ±5pt/30d and ±10pt/182d thresholds. "
            "backend/app/services/ssc_client.py:127-209 (get_score_history(), build_score_summary()).",
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
                "Flag rising slot usage before it hits the licensed cap.",
                f"{usage.slots_used} of {usage.licensed_slots} vendor slots now in use ({pct}%)",
                f"{customer.name} is now using {usage.slots_used} of {usage.licensed_slots} licensed vendor "
                f"slots ({pct}% utilisation). Worth a short conversation about headroom before you reach the "
                "ceiling, so onboarding a new supplier is never delayed by a licence limit.",
                data_source="sample",
                detail=f"{usage.slots_used} of {usage.licensed_slots} licensed vendor slots are now in use "
                "— approaching the licensed ceiling.",
                source_detail="Deterministic placeholder generator, seeded per customer per day — no real "
                "usage feed exists yet. backend/app/services/mock_usage.py:18 (build_usage_summary()).",
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
            "Offer advanced views — usage is well above benchmark.",
            "Your team is using the platform well above benchmark",
            f"{customer.name} logged {total_visits} platform logins this week across {len(usage.individuals)} "
            f"active users — {multiplier} per user, well above our usage benchmark of "
            f"{_BENCHMARK_VISITS_PER_USER:g}. That level of engagement usually means the team is ready for "
            "more advanced views.",
            data_source="sample",
            detail=f"{total_visits} logins this week across {len(usage.individuals)} active users "
            f"— {multiplier} per user, well above the platform benchmark.",
            source_detail="Deterministic placeholder generator, seeded per customer per day — no real "
            "usage feed exists yet. backend/app/services/mock_usage.py:18 (build_usage_summary()).",
        )

    for name in usage.new_individuals[:3]:
        first = name.split(" ")[0]
        card(
            "adoption",
            "1st",
            f"login · {name}",
            "info",
            f"Welcome {first} with a quick platform walkthrough.",
            f"Welcome to SecurityScorecard, {first}",
            f"You logged in to SecurityScorecard for the first time this week. Welcome aboard — you now have "
            f"visibility into {customer.name}'s own rating and its monitored data. Happy to walk you through "
            "the views that matter most for your role.",
            recipient=(name, "New user"),
            data_source="sample",
            detail=f"{name} logged in to SecurityScorecard for the first time.",
            source_detail="Deterministic placeholder generator, compared against the per-customer "
            "seen-individuals cache. backend/app/services/mock_usage.py:18 (build_usage_summary()); "
            f"backend/data/usage_individuals/{customer.id}.json.",
        )

    # --- Questionnaire capacity running low ---
    if usage.questionnaires_licensed > 0:
        remaining_pct = usage.questionnaires_remaining / usage.questionnaires_licensed
        if remaining_pct <= _QUESTIONNAIRE_LOW_REMAINING_PCT:
            card(
                "adoption",
                f"{usage.questionnaires_remaining}/{usage.questionnaires_licensed}",
                "questionnaires remaining",
                "watch",
                "Flag low questionnaire capacity before it limits their vendor assessments.",
                f"{usage.questionnaires_remaining} of {usage.questionnaires_licensed} questionnaires "
                "remaining this cycle",
                f"{customer.name} has {usage.questionnaires_remaining} of {usage.questionnaires_licensed} "
                "licensed questionnaires left this cycle. Worth a short conversation about capacity before "
                "it becomes a blocker for their next vendor assessment.",
                data_source="sample",
                detail=f"Only {usage.questionnaires_remaining} of {usage.questionnaires_licensed} licensed "
                "questionnaires remain this cycle.",
                source_detail="Deterministic placeholder generator, seeded per customer per day — stands in "
                "for the SecurityScorecard Questionnaires (Atlas) API, which isn't integrated yet. "
                "backend/app/services/mock_usage.py:18 (build_usage_summary()).",
            )

    # --- Unused questionnaires expiring soon ---
    if usage.questionnaires_expiring_soon > 0:
        card(
            "adoption",
            str(usage.questionnaires_expiring_soon),
            f"questionnaires expiring in {usage.questionnaires_expiring_in_days}d",
            "watch",
            "Remind them to use expiring questionnaires before they're lost.",
            f"{usage.questionnaires_expiring_soon} unused questionnaires expiring soon",
            f"{customer.name} has {usage.questionnaires_expiring_soon} unused questionnaire"
            f"{'s' if usage.questionnaires_expiring_soon != 1 else ''} expiring in "
            f"{usage.questionnaires_expiring_in_days} days. Worth a quick nudge so they get the value before "
            "the allowance resets.",
            data_source="sample",
            detail=f"{usage.questionnaires_expiring_soon} unused questionnaire"
            f"{'s' if usage.questionnaires_expiring_soon != 1 else ''} expire in "
            f"{usage.questionnaires_expiring_in_days} days.",
            source_detail="Deterministic placeholder generator, seeded per customer per day — stands in for "
            "the SecurityScorecard Questionnaires (Atlas) API, which isn't integrated yet. "
            "backend/app/services/mock_usage.py:18 (build_usage_summary()).",
        )

    # --- Last year's purchase, as an upsell anchor ---
    if customer.last_purchase_product and customer.last_purchase_amount:
        card(
            "adoption",
            f"${customer.last_purchase_amount / 1000:.0f}k",
            "purchased last year",
            "info",
            f"Revisit last year's {customer.last_purchase_product} purchase as an upsell anchor.",
            f"Following up on your {customer.last_purchase_product} purchase",
            f"{customer.name} purchased {customer.last_purchase_product} for "
            f"${customer.last_purchase_amount:,.0f} on {customer.last_purchase_date}. Worth revisiting now "
            "that a year's usage has shown what's working and what they've grown into.",
            badge=customer.last_purchase_product,
            data_source="sample",
            detail=f"Purchased {customer.last_purchase_product} for ${customer.last_purchase_amount:,.0f} "
            f"on {customer.last_purchase_date}.",
            source_detail="Seed data in customers.json (last_purchase_product/date/amount) -- stands in for "
            "a CRM/billing feed we don't have. backend/data/customers.json.",
            csm_only=True,
        )

    # --- Discount: keep it or uplift pricing at renewal, decided from the same usage
    # signals already driving the vendor-slots and engagement triggers above -- not a
    # separate heuristic. ---
    if customer.discount_pct:
        strong_usage = engagement_score >= _ENGAGEMENT_THRESHOLD or (
            usage.licensed_slots > 0 and usage.slots_used / usage.licensed_slots >= _SLOT_CAPACITY_WARN_PCT
        )
        if strong_usage:
            card(
                "adoption",
                f"{customer.discount_pct:.0f}%",
                "discount — uplift?",
                "watch",
                f"Their usage justifies revisiting the {customer.discount_pct:.0f}% discount at renewal.",
                "Checking in ahead of your renewal",
                f"{customer.name} is currently on a {customer.discount_pct:.0f}% discount, but usage this "
                "week shows the account getting real value from the platform. Worth a conversation about "
                "phasing the discount out at renewal rather than rolling it over automatically.",
                data_source="sample",
                detail=f"On a {customer.discount_pct:.0f}% discount with strong current usage — a case for "
                "uplifting price at renewal rather than renewing the discount.",
                source_detail="Discount from customers.json (seed data, stands in for a CRM/billing feed); "
                "usage strength from the same engagement/slot-capacity thresholds as the triggers above. "
                "backend/app/services/opportunities.py.",
                csm_only=True,
            )
        else:
            card(
                "adoption",
                f"{customer.discount_pct:.0f}%",
                "discount — keep it",
                "info",
                f"Hold the {customer.discount_pct:.0f}% discount — usage doesn't support removing it yet.",
                "Checking in ahead of your renewal",
                f"{customer.name} is currently on a {customer.discount_pct:.0f}% discount, and usage this "
                "week doesn't yet show the engagement that would justify removing it. Worth protecting the "
                "renewal by keeping the discount rather than risking churn over price.",
                data_source="sample",
                detail=f"On a {customer.discount_pct:.0f}% discount with usage that doesn't yet support "
                "uplifting price — recommend keeping the discount to protect the renewal.",
                source_detail="Discount from customers.json (seed data, stands in for a CRM/billing feed); "
                "usage strength from the same engagement/slot-capacity thresholds as the triggers above. "
                "backend/app/services/opportunities.py.",
                csm_only=True,
            )

    # --- Expansion: supplier breach anticipated (read-only vendor-detection lookup, no
    # portfolio membership required -- the endpoint returns each vendor's own score) ---
    vendors = ssc_client.get_third_party_vendors(customer.domain, limit=50)
    at_risk_vendors = [
        v
        for v in vendors
        if isinstance(v.get("score"), int)
        and v["score"] < _SUPPLIER_RISK_SCORE_THRESHOLD
        and not _is_ignored_vendor(v.get("company"))
    ]
    if at_risk_vendors:
        worst = min(at_risk_vendors, key=lambda v: v["score"])
        vendor_name = worst.get("company") or worst.get("domain", "A detected supplier")
        card(
            "expansion",
            str(worst["score"]),
            "supplier at risk",
            "watch",
            f"Warn them: {vendor_name} is showing elevated risk.",
            "A supplier in your third-party footprint is showing elevated risk",
            f"{vendor_name}, a supplier detected in {customer.name}'s third-party footprint, is currently "
            f"scoring {worst['score']} on SecurityScorecard — in the at-risk range. Worth flagging and "
            "reviewing exposure before a wider issue develops.",
            detail=f"{vendor_name} ({worst.get('domain', 'unknown domain')}), a supplier detected in "
            f"{customer.name}'s third-party footprint, is currently scoring {worst['score']} — in the "
            "at-risk range.",
            source_detail="SecurityScorecard API — GET /vendor-detection/{domain}/third-party, limit=50, "
            "filtered against a denylist of infrastructure/OSS false-positives. "
            "backend/app/services/ssc_client.py:111-124 (get_third_party_vendors()); "
            "backend/app/services/opportunities.py (_NOT_REAL_VENDORS filter).",
        )

    # --- Expansion: close peer breach anticipated (tracked customers only, anonymised --
    # never name one customer's risk posture to another) ---
    if industry_declines and score.industry:
        peer_declines = [d for d in industry_declines.get(score.industry, []) if d[0] != customer.id]
        if peer_declines:
            _, peer_delta, peer_window = max(peer_declines, key=lambda d: abs(d[1]))
            industry_label = score.industry.replace("_", " ")
            card(
                "expansion",
                str(peer_delta),
                "peer score decline",
                "watch",
                "Raise sector risk proactively — a close peer just declined.",
                "Worth a proactive conversation about sector risk",
                f"A close peer of yours in {industry_label} has seen a notable SSC score decline in the "
                f"last {peer_window}. Without naming names, it's often a sign of sector-wide pressure — "
                "worth a proactive conversation about your own supply-chain exposure in the space.",
                detail=f"A close peer in {industry_label} has seen its SSC score fall {abs(peer_delta)} points "
                f"in the last {peer_window} — worth a proactive conversation about sector exposure.",
                source_detail="SecurityScorecard score history (GET /companies/{domain}/history/score) "
                "compared across other tracked customers sharing this industry field — the peer is never "
                "named. backend/app/routers/opportunities.py:13 (_build_industry_declines()).",
            )

    # --- News (from news research: acquisitions, new offices, product launches). Lives in
    # the "Growing attack surface" lane (group="engagement") -- each of these expands the
    # customer's own footprint (a new entity, office, or product), not a detected vendor
    # relationship, so it's kept separate from "Monitoring Opportunities". ---
    if news:
        for event in _dedupe_news_events(news.events, customer.name)[:5]:
            meta = _NEWS_EVENT_META[event.event_type]
            card(
                "engagement",
                meta["value"],
                meta["label"],
                "info",
                meta["cta"],
                f"{meta['subject_prefix']}: {event.headline}",
                f"{event.summary} {meta['advice']}",
                detected_at=event.date,
                detail=event.summary,
                source_url=event.source_url,
                data_source="researched",
                source_detail="Google News RSS search, extracted into structured events by OpenAI "
                "(gpt-4o-mini). backend/app/services/web_research.py; cached at "
                f"backend/data/news_events/{customer.domain}.json.",
            )

    if decision_makers and decision_makers.people:
        detected_at = decision_makers.imported_at or today_iso
        try:
            detected_at = datetime.fromisoformat(detected_at).date().isoformat()
        except ValueError:
            detected_at = today_iso

        # New decision-makers live in the "Monitoring Opportunities" lane (group="expansion")
        # -- each is an opportunity to bring a new person into engagement/monitoring, same
        # family as the supplier- and peer-risk cards above.
        new_ciso = [p for p in decision_makers.people if p.status == "new" and p.is_ciso_or_biso]
        for p in new_ciso:
            role = "BISO" if "business information security" in p.title.lower() else "CISO"
            card(
                "expansion",
                "NEW",
                f"{role} appointed",
                "info",
                f"Welcome the new {role} with a scorecard handover briefing.",
                f"Congratulations on your appointment as {role}",
                f"Congratulations on your appointment as {role} at {customer.name}. Most incoming {role}s want "
                "a fast, honest read on where things stand — happy to offer a short handover briefing on the "
                "current scorecard and open risk items.",
                detected_at=detected_at,
                recipient=(p.name, p.title),
                detail=f"{p.name} was appointed {p.title}.",
                data_source="researched",
                source_detail="Research prompt run in Claude, pasted back and parsed server-side. "
                "backend/app/services/decision_maker_prompt.py; backend/app/routers/decision_makers.py "
                f"(import endpoint); cached at backend/data/decision_makers/{customer.domain}.json.",
            )

        new_others = [p for p in decision_makers.people if p.status == "new" and not p.is_ciso_or_biso]
        if new_others:
            count = len(new_others)
            for p in new_others:
                card(
                    "expansion",
                    str(count),
                    "new stakeholders",
                    "good",
                    f"Introduce your team to {count} new stakeholder{'s' if count != 1 else ''}.",
                    "Introducing your SecurityScorecard account team",
                    f"You're one of {count} new stakeholders identified in {customer.name}'s security "
                    "decision-making unit. Happy to offer a brief introduction so you have a direct line to "
                    "us alongside the rest of your team.",
                    detected_at=detected_at,
                    recipient=(p.name, p.title),
                    detail=f"{p.name} ({p.title}) newly identified in the decision-making unit — not yet engaged.",
                    data_source="researched",
                    source_detail="Research prompt run in Claude, pasted back and parsed server-side. "
                    "backend/app/services/decision_maker_prompt.py; backend/app/routers/decision_makers.py "
                    f"(import endpoint); cached at backend/data/decision_makers/{customer.domain}.json.",
                )

        # --- Alumni joins another customer (cross-referenced against our own accumulated
        # decision-maker research, no LinkedIn Sales Navigator needed) -- also a "Monitoring
        # Opportunities" card, since it's a new point of contact to bring into engagement. ---
        if person_customer_map:
            for p in decision_makers.people:
                if p.status != "new":
                    continue
                keys = {p.name.strip().lower()}
                if p.linkedin_url:
                    keys.add(p.linkedin_url.strip().lower())
                other_customers = []
                for key in keys:
                    for n in person_customer_map.get(key, []):
                        if n != customer.name and n not in other_customers:
                            other_customers.append(n)
                if not other_customers:
                    continue
                card(
                    "expansion",
                    "ALUMNI",
                    "familiar face",
                    "good",
                    f"Reconnect — they know you from {other_customers[0]}.",
                    f"Great to reconnect via {other_customers[0]}",
                    f"Good to see a familiar face — you were previously part of the security team at "
                    f"{other_customers[0]}, and we're glad to have you at {customer.name} now. Happy to "
                    "pick up where we left off with a quick introduction to your new team's coverage.",
                    detected_at=detected_at,
                    recipient=(p.name, p.title),
                    detail=f"{p.name} ({p.title}) was previously tracked at {other_customers[0]} — now identified "
                    f"at {customer.name}.",
                    source_detail="Matches a newly-identified person's name (or LinkedIn URL) against every "
                    "other tracked customer's cached decision-maker list. "
                    "backend/app/services/opportunities.py (person_customer_map diff, alumni block).",
                    data_source="researched",
                )

    return cards
