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

import json
import os
import re
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
    We still keep the link, though -- it resolves fine in a browser, which is where a
    CSM clicking through from a card actually opens it. Note that <source url> is the
    publisher's homepage, not the article, so the two are captured separately.
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
        link = item.find("link")
        items.append(
            {
                "headline": title.get_text(strip=True) if title else "",
                "published": pub_date.get_text(strip=True) if pub_date else "",
                "publisher": source.get_text(strip=True) if source else "",
                "article_url": link.get_text(strip=True) if link else "",
                "publisher_url": source.get("url") if source and source.get("url") else "",
            }
        )
    return [i for i in items if i["headline"]]


def gather_source_items(queries: list[str], recency: str = "m", limit_per_query: int = 8) -> list[dict]:
    """Deduplicated feed items across every query, in the order they were seen."""
    seen: set[str] = set()
    items: list[dict] = []
    for query in queries:
        for item in search_google_news(query, limit=limit_per_query, recency=recency):
            key = item["headline"].strip().lower()
            if key in seen:
                continue
            seen.add(key)
            items.append(item)
    return items


def build_source_text(items: list[dict]) -> str:
    """Attributed headlines for the extraction step.

    Article URLs are deliberately left out: they're long Google redirect links that
    burn tokens and that the model tends to mangle when echoing back. We reattach the
    real link afterwards by matching on headline -- see _reattach_source_urls.
    """
    if not items:
        return ""
    lines = [
        f"- {i['headline']} (published {i['published']}, via {i['publisher'] or 'unknown'})"
        for i in items
    ]
    return "RECENT NEWS HEADLINES (Google News):\n" + "\n".join(lines)


def gather_source_text(queries: list[str], recency: str = "m", limit_per_query: int = 8) -> str:
    return build_source_text(gather_source_items(queries, recency=recency, limit_per_query=limit_per_query))


def _significant_words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", (text or "").lower()) if len(w) > 3}


def _reattach_source_urls(raw: str, items: list[dict]) -> str:
    """Point each extracted event at the article it came from.

    The model is asked for a source_url but has only headlines to work from, so it
    either returns null or invents a publisher homepage. Match each event back to the
    feed item it most overlaps with and use that item's real link instead.
    """
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    try:
        events = json.loads(text)
    except json.JSONDecodeError:
        return raw
    if not isinstance(events, list):
        return raw

    pool = [(i, _significant_words(i["headline"])) for i in items if i.get("article_url")]
    for event in events:
        if not isinstance(event, dict):
            continue
        target = _significant_words(f"{event.get('headline', '')} {event.get('summary', '')}")
        best, best_score = None, 0.0
        for item, words in pool:
            if not words:
                continue
            # Overlap as a share of the headline's own words, so a short headline
            # isn't penalised for matching against a much longer summary.
            score = len(target & words) / len(words)
            if score > best_score:
                best, best_score = item, score
        # Half the headline in common is a confident match; below that, no link beats
        # a wrong one -- a CSM forwarding the wrong article to a customer is worse.
        event["source_url"] = best["article_url"] if best and best_score >= 0.5 else None
    return json.dumps(events)


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
    items = gather_source_items(queries, recency=recency)
    source_text = build_source_text(items)
    if not source_text.strip():
        return None
    raw = summarise_to_json(prompt, source_text)
    return _reattach_source_urls(raw, items) if raw else raw
