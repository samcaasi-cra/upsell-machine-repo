"""Pseudonymisation for anything sent to a third-party model.

The premise: a score on its own ("91, down 4 over six months") isn't sensitive. A
customer name on its own isn't especially sensitive either. What's sensitive is the two
joined together -- "Stripe is at risk". So we break the link rather than the data:
identities become stable labels, every number and date passes through untouched, and
the agent reasons exactly as well because ranking and thresholds don't care what
something is called.

The hard part isn't the obvious `name` field, it's free text. Signal reasons and news
headlines contain names in prose, so every string is scrubbed against the full entity
list, longest-first so "Monday.com" isn't mangled by a rule for "Monday".

Two honest limits:
- This is pseudonymisation, not anonymisation. Under GDPR the result is still personal
  data, and in a small portfolio context can re-identify ("financial services, top of
  its industry").
- Only the agent path uses this. Research can't: you can't search the news for
  "CUST_A", the real name is the query. That path sends name + domain + public web
  content and no posture, which is roughly what a search engine already sees.
"""

import re
from typing import Any, Optional

from .. import storage


class Pseudonymiser:
    """Built per request from the current roster, so labels are stable within a
    conversation but carry no meaning across them."""

    def __init__(self) -> None:
        self._to_label: dict[str, str] = {}
        self._to_real: dict[str, str] = {}
        self._person_count = 0
        self._build_customer_map()

    # -- map construction -------------------------------------------------

    def _add(self, real: str, label: str) -> None:
        """Several strings can map to one label (display name, domain root, ...), but
        only the first registration defines how that label reads back -- otherwise an
        alias like "notion" would overwrite the canonical "Notion Labs"."""
        real = (real or "").strip()
        if not real or real.lower() in self._to_label:
            return
        self._to_label[real.lower()] = label
        self._to_real.setdefault(label, real)

    def _build_customer_map(self) -> None:
        for i, customer in enumerate(storage.load_customers()):
            label = f"CUST_{chr(65 + i)}" if i < 26 else f"CUST_{i}"
            self._add(customer.name, label)
            self._add(customer.domain, f"{label}.example")
            # Bare second-level name too: "monday.com" -> also catch "monday"
            root = customer.domain.split(".")[0] if customer.domain else ""
            if root and len(root) > 3 and root.lower() != customer.name.lower():
                self._add(root, label)
            # Decision-makers are personal data; the role is what a CSM needs, not the name.
            record = storage.load_decision_makers(customer.domain)
            for person in record.people if record else []:
                self._person_count += 1
                self._add(person.name, f"PERSON_{self._person_count}")

    def add_person(self, name: str) -> str:
        """Register a name discovered mid-request (e.g. a new usage individual)."""
        key = (name or "").strip().lower()
        if key in self._to_label:
            return self._to_label[key]
        self._person_count += 1
        label = f"PERSON_{self._person_count}"
        self._add(name, label)
        return label

    # -- redaction --------------------------------------------------------

    def _scrub_text(self, text: str) -> str:
        """Replace every known identifier appearing anywhere in free text.

        Longest-first so a longer name is consumed before a shorter one that is a
        substring of it. Word-boundary anchored where the term is alphanumeric, so we
        don't corrupt unrelated words.
        """
        result = text
        for real in sorted(self._to_label, key=len, reverse=True):
            label = self._to_label[real]
            if re.search(r"[^\w.\-]", real):  # multi-word: plain case-insensitive replace
                result = re.sub(re.escape(real), label, result, flags=re.IGNORECASE)
            else:
                result = re.sub(rf"\b{re.escape(real)}\b", label, result, flags=re.IGNORECASE)
        return result

    def redact(self, value: Any) -> Any:
        """Recursively pseudonymise a structure. Numbers, dates and booleans are
        untouched -- they're the part the agent actually reasons over."""
        if isinstance(value, str):
            return self._scrub_text(value)
        if isinstance(value, dict):
            return {k: self.redact(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self.redact(v) for v in value]
        return value

    # -- restoration ------------------------------------------------------

    def restore(self, text: str) -> str:
        """Put the real names back before anything reaches the user. Labels the model
        invented that aren't in the map stay pseudonymous, which is the safe direction
        to fail in."""
        result = text
        for label in sorted(self._to_real, key=len, reverse=True):
            result = re.sub(rf"\b{re.escape(label)}\b", self._to_real[label], result)
        return result

    # -- introspection (used by the verification test) --------------------

    def known_identifiers(self) -> list[str]:
        return [self._to_real[label] for label in self._to_real]

    def label_for(self, real: str) -> Optional[str]:
        return self._to_label.get((real or "").strip().lower())
