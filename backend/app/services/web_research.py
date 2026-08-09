"""Automated web research: DuckDuckGo search -> page scrape -> OpenAI summarisation.

Adapted from the working pattern in Cyber_Rescue_Supply_Chain_Crisis_Response_Plan.ipynb
(cells "Breach Report Search" and "GPT Analysis"): same cloudscraper + BeautifulSoup
extraction and the same chat-completion summarisation step.

This is the automated alternative to the copy/paste prompt flow. It reuses the *same*
prompt rule text and the *same* JSON parsers as the manual flow, so both paths produce
identical data -- the only difference is who runs the prompt.

Caveat worth knowing: this depends on scraping DuckDuckGo's HTML results page, which
can break without warning if their markup changes. The manual copy/paste flow remains
available as the fallback.
"""

import os
import urllib.parse
from typing import Optional

import cloudscraper
import requests
from bs4 import BeautifulSoup

from .. import config  # noqa: F401  -- importing this loads .env into the environment

_SEARCH_TIMEOUT = 20
_PAGE_TIMEOUT = 15
_MAX_PAGE_CHARS = 6000

_ANTI_BOT_PHRASES = [
    "Just a moment...",
    "Enable JavaScript and cookies to continue",
    "Please enable cookies.",
    "Checking your browser before accessing",
]

_CONTENT_SELECTORS = [
    "article",
    "main",
    "div.post-content",
    "div.entry-content",
    "div.article-body",
    "div.story-content",
    "div#story-body",
    "div#main-content",
    "div.td-post-content",
    "div#content",
]


def is_configured() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def _scraper():
    return cloudscraper.create_scraper()


def _clean(text: str) -> str:
    for phrase in _ANTI_BOT_PHRASES:
        text = text.replace(phrase, "")
    return text.strip()


# Google News only understands day-granularity windows here -- "when:1m" silently
# returns zero items, so express everything in days.
_RECENCY_TO_GOOGLE = {"d": "1d", "w": "7d", "m": "30d", "y": "365d"}


def search_google_news(query: str, limit: int = 8, recency: str = "m") -> list[dict]:
    """Google News RSS -- returns the feed items themselves (headline, date, publisher),
    not just links.

    Preferred over scraping a results page: it's a real feed endpoint returning XML, so
    there's no anti-bot bypass and no brittle CSS selectors. We use the feed metadata
    directly rather than following the links, because Google News link URLs are
    JS-based redirects that yield no article text when fetched server-side."""
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


def search_duckduckgo(query: str, limit: int = 5, recency: str = "m") -> list[str]:
    """DuckDuckGo HTML search -- fallback when Google News RSS returns nothing (it only
    covers indexed news, so it misses e.g. LinkedIn profiles). `recency`: d/w/m/y."""
    url = f"https://duckduckgo.com/html/?q={urllib.parse.quote(query)}&df={recency}&t=h_&ia=web"
    try:
        html = _scraper().get(url, timeout=_SEARCH_TIMEOUT).text
    except Exception:
        return []
    soup = BeautifulSoup(html, "html.parser")
    urls = []
    for a in soup.select("a.result__a"):
        href = a.get("href")
        if href:
            urls.append(href)
        if len(urls) >= limit:
            break
    return urls


def search_urls(query: str, limit: int = 5, recency: str = "m") -> list[str]:
    """Scrapable result URLs (DuckDuckGo). Google News links are excluded here on
    purpose -- see search_google_news for why they can't be fetched."""
    return search_duckduckgo(query, limit=limit, recency=recency)


def fetch_page_text(url: str) -> str:
    try:
        html = _scraper().get(url, timeout=_PAGE_TIMEOUT).text
    except Exception:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    for selector in _CONTENT_SELECTORS:
        container = soup.select_one(selector)
        if container:
            text = _clean(" ".join(container.stripped_strings))
            if text:
                return text[:_MAX_PAGE_CHARS]
    paragraphs = soup.find_all("p")
    if paragraphs:
        return _clean(" ".join(p.get_text(strip=True) for p in paragraphs))[:_MAX_PAGE_CHARS]
    return _clean(" ".join(soup.stripped_strings))[:_MAX_PAGE_CHARS]


def gather_source_text(
    queries: list[str], per_query: int = 4, recency: str = "m", include_news: bool = True
) -> str:
    """Combine two complementary sources: Google News RSS headlines (reliable, dated,
    attributed -- but headline-only) and scraped DuckDuckGo results (full article text,
    less reliable). Both are labelled so the model can cite them back."""
    chunks: list[str] = []

    if include_news:
        seen_headlines: set[str] = set()
        news_lines: list[str] = []
        for query in queries:
            for item in search_google_news(query, limit=8, recency=recency):
                key = item["headline"].strip().lower()
                if key in seen_headlines:
                    continue
                seen_headlines.add(key)
                news_lines.append(
                    f"- {item['headline']} "
                    f"(published {item['published']}, via {item['publisher'] or 'unknown'}"
                    + (f", {item['source_url']}" if item["source_url"] else "")
                    + ")"
                )
        if news_lines:
            chunks.append("RECENT NEWS HEADLINES (Google News):\n" + "\n".join(news_lines))

    seen_urls: set[str] = set()
    for query in queries:
        for url in search_urls(query, limit=per_query, recency=recency):
            if url in seen_urls:
                continue
            seen_urls.add(url)
            text = fetch_page_text(url)
            if len(text) < 200:  # skip stubs / blocked pages
                continue
            chunks.append(f"SOURCE URL: {url}\n{text}")

    return "\n\n---\n\n".join(chunks)


def summarise_to_json(system_prompt: str, source_text: str, model: str = "gpt-4o-mini") -> str:
    """Send the scraped text plus our existing prompt rules to OpenAI and return the
    raw response, which the caller parses with the same parser the manual flow uses."""
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    from openai import AuthenticationError, RateLimitError

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
        raise RuntimeError(
            "OpenAI rejected the API key. Check OPENAI_API_KEY in backend/.env."
        ) from exc
    return response.choices[0].message.content or ""


def research_to_json(
    prompt: str, queries: list[str], recency: str = "m", include_news: bool = True
) -> Optional[str]:
    """Full pipeline: search + scrape + summarise. Returns the raw JSON string, or None
    if the web research turned up nothing usable to summarise."""
    source_text = gather_source_text(queries, recency=recency, include_news=include_news)
    if not source_text.strip():
        return None
    return summarise_to_json(prompt, source_text)
