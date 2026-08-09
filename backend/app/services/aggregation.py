"""Shared per-customer data gathering, used by both the /signals (risk-sorted table)
and /opportunities (categorized board) endpoints so they stay in sync."""

from .. import storage
from ..models import Customer, DecisionMakerRecord, ScoreSummary, UsageSummary
from . import mock_usage, ssc_client


def gather_all_customer_data() -> list[tuple[Customer, ScoreSummary, UsageSummary, DecisionMakerRecord]]:
    rows = []
    for customer in storage.load_customers():
        score = ssc_client.build_score_summary(customer.domain)
        usage = mock_usage.build_usage_summary(customer.id)
        dm_record = storage.load_decision_makers(customer.domain) or DecisionMakerRecord(
            domain=customer.domain, people=[]
        )
        rows.append((customer, score, usage, dm_record))
    return rows
