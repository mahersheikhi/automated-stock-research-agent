"""Rule-based pullback/recovery screening for research alerts."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services import StockAnalysisResult


@dataclass(frozen=True)
class RecoveryCandidate:
    ticker: str
    price: float
    score: float
    label: str
    five_day_change: float
    horizon: str
    risk_review_price: float
    target_review_price: float
    reasons: list[str]
    reference_url: str


def evaluate_recovery(result: "StockAnalysisResult") -> RecoveryCandidate | None:
    """Identify a recent pullback with evidence worth researching further.

    This is deliberately an evidence score, not a buy recommendation or a
    prediction that a fallen asset will recover.
    """
    if result.five_day_change is None or result.five_day_change > -1:
        return None

    score = result.final_score * 0.35
    reasons = [f"Five-day move: {result.five_day_change:.1f}%."]

    if -15 <= result.five_day_change <= -3:
        score += 20
        reasons.append("Recent pullback is meaningful but not an extreme breakdown.")
    elif result.five_day_change < -15:
        score += 5
        reasons.append("Large decline increases uncertainty; require extra confirmation.")

    if 30 <= result.rsi <= 45:
        score += 20
        reasons.append("RSI is in a possible recovery zone.")
    elif 45 < result.rsi <= 52:
        score += 10
        reasons.append("RSI is improving toward neutral.")

    if result.support and result.price <= result.support * 1.06:
        score += 15
        reasons.append("Price is close to recent support.")
    if result.macd > result.macd_signal:
        score += 10
        reasons.append("MACD is above its signal line.")
    if result.news_score is not None and result.news_score >= 60:
        score += 10
        reasons.append("Recent headline sentiment is positive.")
    if result.trend == "Bearish":
        score -= 10
        reasons.append("The medium-term trend remains bearish.")

    score = max(0.0, min(100.0, score))
    if score >= 70:
        label = "Stronger recovery watch"
    elif score >= 55:
        label = "Potential recovery watch"
    else:
        label = "High-risk recovery watch"

    horizon = {
        "Bullish": "2–6 weeks; reassess weekly.",
        "Mixed": "1–3 weeks; reassess after the next few sessions.",
        "Bearish": "3–10 trading days; high caution and frequent review.",
    }.get(result.trend, "1–3 weeks; reassess frequently.")
    risk_review = max(0.01, result.support - (result.atr * 0.5))
    target_review = result.resistance or result.price

    return RecoveryCandidate(
        ticker=result.ticker,
        price=result.price,
        score=round(score, 1),
        label=label,
        five_day_change=round(result.five_day_change, 1),
        horizon=horizon,
        risk_review_price=round(risk_review, 2),
        target_review_price=round(target_review, 2),
        reasons=reasons[:3],
        reference_url=(result.references or {}).get("Yahoo Finance", ""),
    )
