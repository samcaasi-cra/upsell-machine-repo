"""Automated web research: Google News RSS -> OpenAI extraction.

Originally this also scraped DuckDuckGo's HTML results via cloudscraper, adapted from
Cyber_Rescue_Supply_Chain_Crisis_Response_Plan.ipynb. That half has been removed:

- It stopped working. DuckDuckGo rate-limited us after modest use, returning zero
  results for queries that had worked minutes earlier.
- cloudscraper exists specifically to defeat bot detection, which is against DDG's
  terms and not something that should sit in a production path.
- It added little. Google News RSS is a real feed endpoint returning structured XML
  with headlines, dates and publishers -- enough for the extraction step to identify
  acquisitions, office openings and product launches.

This is the automated alternative to the copy/paste prompt flow. It reuses the *same*
prompt rule text and the *same* JSON parsers as the manual flow, so both paths produce
identical data -- the only difference is who runs the prompt.
"""

import os
import urllib.parse

import requests
from bs4 import BeautifulSoup

from .. import config  # noqa: F401  -- importing this loads .env into the environment

_SEARCH_TIMEOUT = 20

# Google News only understands day-granularity windows here -- "when:1m" silently
# returns zero items, so express everything in days.
_RECENCY_TO_GOOGLE = {"d": "1d", "w": "7d", "m": "30d", "y": "365d"}


def is_configured() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def search_google_news(query: str, limit: int = 8, recency: str = "m") -> list[dict]:
    """Google News RSS -- returns the feed items themselves (headline, date, publisher).

    We use the feed metadata directly rather than following the links: Google News link
    URLs are JS-based redirects that yield no article text when fetched server-side.
    """
    when = _RECENCY_TO_GOOGLE.get(recency, "30d")
    q = urllib.parse.quote_plus(f"{query} when:{when}")
    url = f"https://news.google.com/rss/search?q={q}&hl=en-GB&gl=GB&ceid=GB:en"
    try:
        resp = requests.get(url, timeout=_SEARCH_TIMEOUT, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(resp.text, "xml")
    items = []
    for item in soup.find_all("item")[:limit]:
        title = item.find("title")
        pub_date = item.find("pubDate")
        source = item.find("source")
        items.append(
            {
                "headline": title.get_text(strip=True) if title else "",
                "published": pub_date.get_text(strip=True) if pub_date else "",
                "publisher": source.get_text(strip=True) if source else "",
                "source_url": source.get("url") if source and source.get("url") else "",
            }
        )
    return [i for i in items if i["headline"]]


def gather_source_text(queries: list[str], recency: str = "m", limit_per_query: int = 8) -> str:
    """Deduplicated, attributed headlines across every query, labelled so the
    extraction step can cite them back."""
    seen: set[str] = set()
    lines: list[str] = []
    for query in queries:
        for item in search_google_news(query, limit=limit_per_query, recency=recency):
            key = item["headline"].strip().lower()
            if key in seen:
                continue
            seen.add(key)
            lines.append(
                f"- {item['headline']} "
                f"(published {item['published']}, via {item['publisher'] or 'unknown'}"
                + (f", {item['source_url']}" if item["source_url"] else "")
                + ")"
            )
    if not lines:
        return ""
    return "RECENT NEWS HEADLINES (Google News):\n" + "\n".join(lines)


def summarise_to_json(system_prompt: str, source_text: str, model: str = "gpt-4o-mini") -> str:
    """Send the gathered headlines plus our existing prompt rules to OpenAI and return
    the raw response, which the caller parses with the same parser the manual flow uses."""
    from openai import AuthenticationError, OpenAI, RateLimitError

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    client = OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You extract structured JSON from web research. Return JSON only, no prose.",
                },
                {"role": "user", "content": f"{system_prompt}\n\nRESEARCH SOURCE TEXT:\n{source_text}"},
            ],
            response_format={"type": "json_object"},
        )
    except RateLimitError as exc:
        raise RuntimeError(
            "OpenAI rejected the request for quota reasons — the account may be out of credits. "
            "Check billing at platform.openai.com, or use the copy/paste research flow instead."
        ) from exc
    except AuthenticationError as exc:
        raise RuntimeError("OpenAI rejected the API key. Check OPENAI_API_KEY in backend/.env.") from exc
    return response.choices[0].message.content or ""


def research_to_json(
    prompt: str, queries: list[str], recency: str = "m", include_news: bool = True
) -> str | None:
    """Full pipeline: search + extract. Returns the raw JSON string, or None if the
    search turned up nothing to work with.

    `include_news` is retained for call-site compatibility; news is now the only
    source, so passing False simply means there's nothing to gather.
    """
    if not include_news:
        return None
    source_text = gather_source_text(queries, recency=recency)
    if not source_text.strip():
        return None
    return summarise_to_json(prompt, source_text)
