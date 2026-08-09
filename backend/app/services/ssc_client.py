"""SecurityScorecard API client.

Adapted from the working call pattern in Updated_BA_Animation_Tool_6th_August_2026.ipynb
(cell "SSC API CALL" and the commented "High Scoring Firm" cell): same auth header shape
and the same `/history/score` endpoint, simplified here to single-domain lookups instead
of portfolio batch uploads, since the dashboard only needs one company at a time.
"""

import time
from datetime import datetime, timedelta
from typing import Optional

import requests

from .. import config
from ..models import ScorePoint, ScoreSummary

_HEADERS = {
    "Authorization": f"Token {config.SSC_API_KEY}",
    "accept": "application/json; charset=utf-8",
}

_TIMEOUT = 15
_CACHE_TTL_SECONDS = 600
_cache: dict[str, tuple[float, dict]] = {}

# Domains must belong to a portfolio before /companies/{domain} or its history can be
# queried. We keep exactly one shared (org-visible) portfolio for this dashboard's demo
# domains -- never private, per team policy -- and add domains to it lazily on first use.
PORTFOLIO_NAME = "Upsell Machine Dashboard - Demo Domains - Do Not Delete"
_portfolio_id: Optional[str] = None
_domains_in_portfolio: set[str] = set()


def _cached_get(url: str, params: Optional[dict] = None) -> dict:
    cache_key = url + "?" + str(sorted((params or {}).items()))
    now = time.time()
    if cache_key in _cache:
        cached_at, data = _cache[cache_key]
        if now - cached_at < _CACHE_TTL_SECONDS:
            return data

    resp = requests.get(url, headers=_HEADERS, params=params, timeout=_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    _cache[cache_key] = (now, data)
    return data


def get_or_create_portfolio() -> str:
    """Reuse the dashboard's shared portfolio if it already exists, else create it."""
    global _portfolio_id
    if _portfolio_id:
        return _portfolio_id

    resp = requests.get(f"{config.SSC_BASE_URL}/portfolios", headers=_HEADERS, timeout=_TIMEOUT)
    resp.raise_for_status()
    for entry in resp.json().get("entries", []):
        if entry.get("name") == PORTFOLIO_NAME:
            _portfolio_id = entry["id"]
            return _portfolio_id

    resp = requests.post(
        f"{config.SSC_BASE_URL}/portfolios",
        headers=_HEADERS,
        json={"name": PORTFOLIO_NAME, "privacy": "shared"},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    _portfolio_id = resp.json()["id"]
    return _portfolio_id


def ensure_domain_in_portfolio(domain: str) -> None:
    if domain in _domains_in_portfolio:
        return
    portfolio_id = get_or_create_portfolio()
    resp = requests.put(
        f"{config.SSC_BASE_URL}/portfolios/{portfolio_id}/companies/{domain}",
        headers=_HEADERS,
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    _domains_in_portfolio.add(domain)


def get_company(domain: str) -> dict:
    """Current score/grade snapshot for a domain via GET /companies/{domain}."""
    return _cached_get(f"{config.SSC_BASE_URL}/companies/{domain}")


def get_score_history(domain: str, days: int = 190, timing: str = "weekly") -> list[dict]:
    """Historical score points via GET /companies/{domain}/history/score."""
    to_date = datetime.today()
    from_date = to_date - timedelta(days=days)
    data = _cached_get(
        f"{config.SSC_BASE_URL}/companies/{domain}/history/score",
        params={
            "timing": timing,
            "from": from_date.strftime("%Y-%m-%d"),
            "to": to_date.strftime("%Y-%m-%d"),
        },
    )
    entries = data.get("entries", [])
    return [{"date": e["date"][:10], "score": e["score"]} for e in entries]


def _score_closest_to(history: list[dict], target_date: datetime) -> Optional[int]:
    if not history:
        return None
    best = min(
        history,
        key=lambda pt: abs((datetime.strptime(pt["date"], "%Y-%m-%d") - target_date).days),
    )
    # Only trust it as a "N days ago" reference if it's within ~10 days of the target,
    # otherwise the history simply doesn't go back far enough.
    if abs((datetime.strptime(best["date"], "%Y-%m-%d") - target_date).days) > 10:
        return None
    return best["score"]


def build_score_summary(domain: str) -> ScoreSummary:
    """Fetch current + historical SSC scores for a domain and compute the deliverable's
    exact threshold flags: +/-5 pts in 30 days, +/-10 pts in 182 days, score > 95."""
    try:
        ensure_domain_in_portfolio(domain)
        company = get_company(domain)
        history = get_score_history(domain, days=190)
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "?"
        detail = ""
        try:
            detail = exc.response.json().get("error", {}).get("message", "")
        except Exception:
            pass
        return ScoreSummary(domain=domain, error=f"SecurityScorecard API error ({status}) {detail}".strip())
    except requests.RequestException as exc:
        return ScoreSummary(domain=domain, error=f"SecurityScorecard request failed: {exc}")

    current_score = company.get("score")
    current_grade = company.get("grade")
    industry = company.get("industry")
    today = datetime.today()

    score_30d_ago = _score_closest_to(history, today - timedelta(days=30))
    score_182d_ago = _score_closest_to(history, today - timedelta(days=182))

    delta_30d = (current_score - score_30d_ago) if (current_score is not None and score_30d_ago is not None) else None
    delta_182d = (
        (current_score - score_182d_ago) if (current_score is not None and score_182d_ago is not None) else None
    )

    flags: list[str] = []
    if delta_30d is not None and delta_30d > 5:
        flags.append("score_up_5_30d")
    if delta_30d is not None and delta_30d < -5:
        flags.append("score_down_5_30d")
    if delta_182d is not None and delta_182d > 10:
        flags.append("score_up_10_182d")
    if delta_182d is not None and delta_182d < -10:
        flags.append("score_down_10_182d")
    if current_score is not None and current_score > 95:
        flags.append("score_above_95")

    return ScoreSummary(
        domain=domain,
        current_score=current_score,
        current_grade=current_grade,
        industry=industry,
        history=[ScorePoint(**pt) for pt in history],
        delta_30d=delta_30d,
        delta_182d=delta_182d,
        flags=flags,
    )
