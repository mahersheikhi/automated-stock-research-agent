from __future__ import annotations

from app.models import DecisionResult, SourceLink, TechnicalResult, FundamentalResult, NewsResult, RiskResult


def make_decision(ticker: str, technical: TechnicalResult, fundamentals: FundamentalResult, news: NewsResult, risk: RiskResult) -> DecisionResult:
    components = {
        "technical": technical.score,
        "fundamental": fundamentals.score,
        "news": news.score,
        "risk": risk.score,
    }
    final = round(
        technical.score * 0.35 + fundamentals.score * 0.25 + news.score * 0.25 + risk.score * 0.15,
        1,
    )
    if final >= 75:
        decision = "Strong watch / possible buy candidate"
        confidence = "High"
    elif final >= 63:
        decision = "Watch / possible buy on good entry"
        confidence = "Medium"
    elif final >= 50:
        decision = "Neutral / wait"
        confidence = "Medium"
    else:
        decision = "Avoid for now"
        confidence = "Low"

    reasons = []
    reasons.append(f"Technical setup: {technical.trend} ({technical.score}/100).")
    reasons.append(f"Fundamentals score: {fundamentals.score}/100.")
    reasons.append(f"Recent news sentiment: {news.sentiment} ({news.score}/100).")
    reasons.append(f"Risk setup score: {risk.score}/100.")

    sources: list[SourceLink] = []
    for block in (technical, fundamentals, news, risk):
        sources.extend(block.sources)

    return DecisionResult(
        ticker=ticker,
        final_score=final,
        decision=decision,
        confidence=confidence,
        reasons=reasons,
        sources=sources,
        components=components,
    )
