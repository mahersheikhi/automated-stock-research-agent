"""Explainable, headline-based news sentiment analysis."""
from __future__ import annotations

from dataclasses import dataclass

from providers.google_news import NewsItem, fetch_news


POSITIVE_TERMS = {
    "beat": 2,
    "beats": 2,
    "bullish": 2,
    "contract": 1,
    "growth": 1,
    "outperform": 2,
    "partnership": 1,
    "profit": 1,
    "raise": 1,
    "raises": 1,
    "record": 1,
    "strong": 1,
    "surge": 2,
    "upgrade": 2,
}
NEGATIVE_TERMS = {
    "bearish": 2,
    "cut": 1,
    "cuts": 1,
    "downgrade": 2,
    "fall": 1,
    "investigation": 2,
    "lawsuit": 2,
    "loss": 1,
    "miss": 2,
    "probe": 2,
    "slowdown": 1,
    "warning": 1,
    "weak": 1,
}


@dataclass(frozen=True)
class NewsAnalysis:
    ticker: str
    score: float
    sentiment: str
    summary: str
    article_count: int
    items: list[NewsItem]


def analyze_news(ticker: str) -> NewsAnalysis:
    """Score recent Google News headlines without presenting them as a forecast."""
    items, _ = fetch_news(ticker)
    if not items:
        return NewsAnalysis(
            ticker=ticker.upper(),
            score=50.0,
            sentiment="Unavailable",
            summary="No recent Google News headlines were available for scoring.",
            article_count=0,
            items=[],
        )

    positive_hits = 0
    negative_hits = 0
    for item in items:
        headline = item.title.lower()
        positive_hits += sum(weight for term, weight in POSITIVE_TERMS.items() if term in headline)
        negative_hits += sum(weight for term, weight in NEGATIVE_TERMS.items() if term in headline)

    # A bounded headline signal: neutral is 50; several consistent signals can
    # move the score, while one sensational headline cannot dominate the scan.
    score = max(0.0, min(100.0, 50.0 + (positive_hits - negative_hits) * 5.0))
    if score >= 58:
        sentiment = "Positive"
    elif score <= 42:
        sentiment = "Negative"
    else:
        sentiment = "Neutral"

    summary = (
        f"{len(items)} recent headlines: {positive_hits} positive and "
        f"{negative_hits} negative keyword signals."
    )
    return NewsAnalysis(
        ticker=ticker.upper(),
        score=round(score, 1),
        sentiment=sentiment,
        summary=summary,
        article_count=len(items),
        items=items,
    )
