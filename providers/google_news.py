from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote_plus

import feedparser
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class NewsItem:
    title: str
    link: str
    source: str
    published: str
    summary: str


def _clean_html(text: str) -> str:
    return BeautifulSoup(text or "", "html.parser").get_text(" ", strip=True)


def google_news_rss_url(query: str) -> str:
    return f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"


def fetch_news(ticker: str, limit: int = 8) -> tuple[list[NewsItem], str]:
    query = f"{ticker} stock earnings analyst outlook"
    url = google_news_rss_url(query)
    feed = feedparser.parse(url)
    items: list[NewsItem] = []
    for entry in feed.entries[:limit]:
        source = getattr(getattr(entry, "source", None), "title", "Google News")
        items.append(
            NewsItem(
                title=_clean_html(getattr(entry, "title", "")),
                link=getattr(entry, "link", ""),
                source=source or "Google News",
                published=getattr(entry, "published", ""),
                summary=_clean_html(getattr(entry, "summary", "")),
            )
        )
    return items, url
