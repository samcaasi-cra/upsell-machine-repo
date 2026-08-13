"""Sample usage data standing in for deliverable #1's platform usage webhooks / CRM
feed, which aren't wired up yet. Seeded per customer *and* per day so numbers stay
stable across reloads within a day (no jitter on refresh) but still drift day to day,
which is what lets the "new user logged in for the first time" trigger (#21) mean
something rather than being permanently frozen."""

import random
from datetime import date

from .. import storage
from ..models import UsageIndividual, UsageSummary

_FIRST_NAMES = ["Alex", "Priya", "Jordan", "Mei", "Sam", "Nina", "Theo", "Ola", "Freya", "Ravi"]
_LAST_NAMES = ["Chen", "Okafor", "Silva", "Novak", "Rahman", "Berg", "Kowalski", "Diallo"]
_LICENSE_TIERS = [8, 10, 12, 15, 20]
_QUESTIONNAIRE_TIERS = [10, 15, 20, 25, 30]


def build_usage_summary(customer_id: str) -> UsageSummary:
    # Capacity is a property of the contract, not the day -- seeded by customer only.
    cap_rng = random.Random(customer_id)
    licensed_slots = cap_rng.choice(_LICENSE_TIERS)
    questionnaires_licensed = cap_rng.choice(_QUESTIONNAIRE_TIERS)

    # Everything else is seeded per customer *and* day.
    rng = random.Random(f"{customer_id}:{date.today().isoformat()}")

    slots_filled_7d = rng.randint(0, min(8, licensed_slots))
    slots_delta_7d = slots_filled_7d - rng.randint(0, min(8, licensed_slots))
    # Total slots currently in use out of the licensed cap -- occasionally pushed near
    # the ceiling so trigger #1 (nearing full utilisation) has something to catch.
    slots_used = min(licensed_slots, rng.randint(0, int(licensed_slots * 1.15)))

    reports_generated_7d = rng.randint(0, 20)
    reports_delta_7d = reports_generated_7d - rng.randint(0, 20)

    num_individuals = rng.randint(3, 6)
    names = []
    while len(names) < num_individuals:
        name = f"{rng.choice(_FIRST_NAMES)} {rng.choice(_LAST_NAMES)}"
        if name not in names:
            names.append(name)
    individuals = [UsageIndividual(name=n, visits_7d=rng.randint(0, 15)) for n in names]

    known = set(storage.load_known_individuals(customer_id))
    new_individuals = [n for n in names if n not in known]
    storage.save_known_individuals(customer_id, sorted(known | set(names)))

    # Same trick as slots_used above: draw "completed" from a range that occasionally
    # exceeds the cap, so remaining sometimes lands low or at zero without a second
    # explicit branch.
    questionnaires_completed = rng.randint(0, questionnaires_licensed + 5)
    questionnaires_remaining = max(0, questionnaires_licensed - questionnaires_completed)
    # A minority of days, some of what's left is about to expire unused.
    questionnaires_expiring_soon = (
        rng.randint(1, questionnaires_remaining) if questionnaires_remaining > 0 and rng.random() < 0.4 else 0
    )
    questionnaires_expiring_in_days = rng.randint(5, 45) if questionnaires_expiring_soon > 0 else 0

    return UsageSummary(
        slots_filled_7d=slots_filled_7d,
        slots_delta_7d=slots_delta_7d,
        reports_generated_7d=reports_generated_7d,
        reports_delta_7d=reports_delta_7d,
        licensed_slots=licensed_slots,
        slots_used=slots_used,
        individuals=individuals,
        new_individuals=new_individuals,
        questionnaires_licensed=questionnaires_licensed,
        questionnaires_remaining=questionnaires_remaining,
        questionnaires_expiring_soon=questionnaires_expiring_soon,
        questionnaires_expiring_in_days=questionnaires_expiring_in_days,
    )
