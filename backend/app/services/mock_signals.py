"""Illustrative cards for four signal sources we don't have real integrations for yet:
email correspondence, Salesforce, support tickets, and customer surveys.

Unlike `concept_triggers.py`, these are visible by default -- they're a real addition
to the board (the "Change at Customer" lane -- these are all relationship/organisation
signals, not raw platform-usage metrics), just backed by invented data until each
integration exists. Every card is tagged data_source="mockup" and carries a badge
naming the source, so it can never be mistaken for a live signal.

Each spec is deterministically assigned to two customers by roster position, so the
demo is stable across reloads without stamping every source onto every account.
"""

import hashlib
from datetime import date, timedelta
from typing import Optional

from ..models import Customer, OpportunityCard, RecipientOption


def _card_id(customer_id: str, source: str) -> str:
    return "mock-" + hashlib.sha1(f"{customer_id}|{source}".encode()).hexdigest()[:12]


def _recipient(customer: Customer) -> tuple[str, str]:
    if customer.sponsor:
        return customer.sponsor, "Sponsor"
    return "Primary Contact", "Primary Contact"


def _card(customer: Customer, source: str, days_ago: int, **fields) -> OpportunityCard:
    recipient_name, recipient_role = _recipient(customer)
    first = recipient_name.split(" ")[0] if recipient_name != "Primary Contact" else "there"
    signer = customer.csm or "The SecurityScorecard Customer Success Team"
    return OpportunityCard(
        card_id=_card_id(customer.id, source),
        group="engagement",
        customer_id=customer.id,
        customer_name=customer.name,
        data_source="mockup",
        detected_at=(date.today() - timedelta(days=days_ago)).isoformat(),
        recipient_name=recipient_name,
        recipient_role=recipient_role,
        recipient_options=[RecipientOption(name=recipient_name, role=recipient_role)],
        body=f"Hello {first},\n\n{fields.pop('body_intro')}\n\nKind regards,\n{signer}\n"
        "SecurityScorecard Customer Success",
        **fields,
    )


def _email_card(customer: Customer) -> OpportunityCard:
    return _card(
        customer,
        "email",
        days_ago=2,
        value="EMAIL",
        label="email correspondence",
        sentiment="info",
        description="Follow up on their email asking about advanced reporting.",
        subject="Following up on your question about advanced reporting",
        body_intro="Thanks for reaching out about advanced reporting options — happy to walk you through "
        "what's available on your current plan and what an upgrade would unlock.",
        detail=f"{customer.name} emailed asking whether advanced/scheduled reporting is available on their "
        "current plan.",
        badge="Mockup — Email correspondence",
        source_detail="Not built yet. Proposed source: SecurityScorecard-customer email threads (e.g. a "
        "shared inbox or Gmail/Outlook API integration).",
    )


def _salesforce_card(customer: Customer) -> OpportunityCard:
    return _card(
        customer,
        "salesforce",
        days_ago=1,
        value="SFDC",
        label="Salesforce signal",
        sentiment="info",
        description="Reach out — Salesforce shows this account entering its renewal window with an open "
        "expansion opportunity.",
        subject="Checking in ahead of your renewal",
        body_intro="Wanted to check in as your renewal approaches — happy to talk through where the "
        "platform could go further for your team.",
        detail=f"Salesforce shows {customer.name}'s account moving into its renewal window, with an "
        "expansion opportunity logged on the account.",
        badge="Mockup — Salesforce",
        source_detail="Not built yet. Proposed source: Salesforce CRM (opportunity stage and renewal-date "
        "fields).",
        csm_only=True,
    )


def _support_ticket_card(customer: Customer) -> OpportunityCard:
    return _card(
        customer,
        "tickets",
        days_ago=4,
        value="3",
        label="support tickets",
        sentiment="info",
        description="Ensure they receive a positive resolution — repeated tickets suggest friction.",
        subject="Following up on your recent support tickets",
        body_intro="Noticed a few recent tickets asking about single sign-on — that's usually a sign a "
        "team's ready to move up a tier, happy to talk through it.",
        detail=f"{customer.name} submitted 3 support tickets this month asking about single sign-on (SSO), "
        "a feature not included on their current plan.",
        badge="Mockup — Support tickets",
        source_detail="Not built yet. Proposed source: support/helpdesk ticketing system (e.g. Zendesk).",
    )


def _survey_card(customer: Customer) -> OpportunityCard:
    return _card(
        customer,
        "survey",
        days_ago=7,
        value="9/10",
        label="satisfaction survey",
        sentiment="good",
        description="Cite their strong survey response as renewal proof.",
        subject="Thank you for the feedback",
        body_intro="Thanks for the great feedback in your latest satisfaction survey — glad the automated "
        "reports are saving your team time. Worth documenting this ahead of renewal.",
        detail=f"{customer.name} scored the platform 9/10 in the latest satisfaction survey, citing "
        "automated reports as especially valuable.",
        badge="Mockup — Customer survey",
        source_detail="Not built yet. Proposed source: a post-interaction customer satisfaction survey "
        "(e.g. NPS/CSAT tool).",
    )


_SPECS = [
    ({0, 1}, _email_card),
    ({2, 3}, _salesforce_card),
    ({4, 5}, _support_ticket_card),
    ({6, 7}, _survey_card),
]


def build_mock_signal_cards(customer: Customer, roster_index: int) -> list[OpportunityCard]:
    for indices, builder in _SPECS:
        if roster_index in indices:
            return [builder(customer)]
    return []
