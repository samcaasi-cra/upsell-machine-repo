"""Sample usage data standing in for deliverable #1's platform usage webhooks / CRM
feed, which aren't wired up yet. Seeded by customer id so numbers stay stable across
dashboard reloads instead of jittering randomly every request."""

import random

from ..models import UsageIndividual, UsageSummary

_FIRST_NAMES = ["Alex", "Priya", "Jordan", "Mei", "Sam", "Nina", "Theo", "Ola"]
_LAST_NAMES = ["Chen", "Okafor", "Silva", "Novak", "Rahman", "Berg", "Kowalski"]


def build_usage_summary(customer_id: str) -> UsageSummary:
    rng = random.Random(customer_id)

    slots_filled_7d = rng.randint(0, 8)
    slots_delta_7d = slots_filled_7d - rng.randint(0, 8)

    reports_generated_7d = rng.randint(0, 20)
    reports_delta_7d = reports_generated_7d - rng.randint(0, 20)

    num_individuals = rng.randint(3, 6)
    individuals = []
    for _ in range(num_individuals):
        name = f"{rng.choice(_FIRST_NAMES)} {rng.choice(_LAST_NAMES)}"
        individuals.append(UsageIndividual(name=name, visits_7d=rng.randint(0, 15)))

    return UsageSummary(
        slots_filled_7d=slots_filled_7d,
        slots_delta_7d=slots_delta_7d,
        reports_generated_7d=reports_generated_7d,
        reports_delta_7d=reports_delta_7d,
        individuals=individuals,
    )
