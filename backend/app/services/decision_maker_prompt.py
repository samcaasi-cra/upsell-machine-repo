"""Generates a copy/paste research prompt for deliverable #2 (decision-maker /
job-title tracking) and parses the JSON pasted back in.

Adapted from the user-supplied "one-page cover page .docx" Claude prompt: all of the
substantive research and selection rules are kept (employment test, fit test, title
evidence hierarchy, LinkedIn URL verification, function-level caps, CISO/BISO priority
order, low-count expansion, alphabetical sort, minimum/target/maximum counts), but the
entire DOCX layout/typography/table-width section is replaced with an instruction to
return JSON only. No LLM API is called here -- the user runs this prompt themselves in
Claude and pastes the result back in via the import endpoint.
"""

import json
import re
from typing import List, Optional

from ..models import DecisionMaker

_JSON_SCHEMA_HINT = """{
  "people": [
    {
      "name": "Full Name",
      "title": "Exact current company job title",
      "linkedin_url": "https://www.linkedin.com/in/... or null if not reliably known",
      "primary_focus": "Cyber Security | Third Party Risk Management | Risk / Governance / Compliance | Internal Audit | Privacy | Legal | Business Continuity / Resilience | IT Services / Technology Controls | Supplier / Procurement / Supply Chain Assurance | Cyber Training & Competence",
      "is_ciso_or_biso": true
    }
  ]
}"""


def build_prompt(company_name: str, domain: str, existing_names: Optional[List[str]] = None) -> str:
    existing_block = "(none supplied)"
    if existing_names:
        existing_block = "\n".join(f"- {n}" for n in existing_names)

    return f"""Research the current internal Governance, Risk, Compliance, Internal Audit, Third
Party Risk / Supplier Risk / Vendor Risk, and Cyber Security / Information Security
decision-makers at the company behind this domain, using only public sources.

COMPANY: {company_name}
DOMAIN: {domain}

EXISTING_NAMES (treat as confirmed inclusions -- research their current title and
LinkedIn URL and include them regardless of function caps):
{existing_block}

SELECTION RULES
- Only include a person if BOTH are true: (1) strong public evidence they currently
  work at this company, and (2) their current role clearly and directly maps to one of
  the target functions below. If in doubt, exclude.
- Target functions: Cyber Security / Information Security / Security Engineering /
  Security Operations; Third Party Risk Management / Supplier Risk / Vendor Risk;
  Risk / Governance / Compliance; Internal Audit; Business Continuity / Resilience;
  Privacy (only in an internal control role); Legal (only in an internal governance /
  compliance control role); IT Services / Technology Controls (only where it materially
  affects cyber risk, security, or resilience); Supplier / Procurement / Supply Chain
  Assurance (map to Third Party Risk Management when it affects supplier/third-party
  risk); Cyber Training & Competence (only when specifically about cyber training or
  cyber competence).
- Exclude anyone whose fit is indirect, inferred, stale, or merely senior/visible with
  no clear control-function remit (e.g. regional director, general commercial/sales/
  product/ops leadership, board member with no direct control-function role).
- Make a specific effort to identify the current CISO. If none is identifiable, find the
  current BISO. If neither, find the closest clearly evidenced senior internal
  cyber-security leader. Always include this person.
- Title evidence hierarchy (highest to lowest trust): (1) current official company page,
  (2) current LinkedIn current-role field/snippet, (3) other strong current public
  source, (4) LinkedIn headline/summary/tagline -- level 4 may only be used to judge fit,
  never as the displayed job title, and never to upgrade a title's seniority (e.g. never
  turn "Manager" into "Head", "Head" into "Director", or any role into "CISO"/"BISO"
  without exact evidence).
- LinkedIn URL: only attach a personal profile URL if you are confident it is the exact
  person's own profile (not a directory, search page, or guess). Otherwise leave it null
  -- do not omit a person for lacking one, and do not guess a URL.
- Function-level maximums for the final list: Cyber Security up to 4; Third Party Risk
  Management up to 3; every other function up to 2. Prefer 3-4 Cyber Security people and
  2-3 Third Party Risk Management people where publicly identifiable.
- Target 8-10 people total (minimum 3, maximum 12). If a direct-fit search produces
  fewer than 6, broaden to strong adjacent roles (e.g. Head of IT Services, procurement/
  supply-chain/supplier-quality leadership, cyber training & competence roles) before
  settling for fewer than 6 -- but never invent people or include weak/unrelated fits
  just to hit a target count.
- Sort the final list alphabetically by first name.

OUTPUT FORMAT -- IMPORTANT
Return ONLY a single JSON object matching this exact shape, no prose before or after it,
no markdown code fences:

{_JSON_SCHEMA_HINT}

Do not generate a Word document or any other file -- structured JSON only."""


def parse_import(raw_text: str) -> List[DecisionMaker]:
    """Parse the JSON a user pastes back from running the prompt above. Tolerates
    markdown code fences since that's how it usually gets copied out of a chat."""
    text = raw_text.strip()
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence_match:
        text = fence_match.group(1).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"That doesn't look like valid JSON: {exc}") from exc

    if isinstance(data, dict) and "people" in data:
        people_raw = data["people"]
    elif isinstance(data, list):
        people_raw = data
    else:
        raise ValueError('Expected a JSON object with a "people" array, or a JSON array of people.')

    if not isinstance(people_raw, list) or not people_raw:
        raise ValueError("No people found in the pasted result.")

    people: List[DecisionMaker] = []
    for i, item in enumerate(people_raw):
        try:
            people.append(DecisionMaker(**item))
        except Exception as exc:
            raise ValueError(f"Person #{i + 1} doesn't match the expected shape: {exc}") from exc
    return people
