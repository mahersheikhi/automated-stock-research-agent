from __future__ import annotations

from app.models import FundamentalResult, SourceLink
from providers.yahoo import get_ticker_info, yahoo_quote_url
from utils import clamp, pct


def analyze_fundamentals(ticker: str) -> FundamentalResult:
    info = get_ticker_info(ticker)
    pe = info.get("trailingPE") or info.get("forwardPE")
    revenue_growth = info.get("revenueGrowth")
    profit_margin = info.get("profitMargins")
    debt_to_equity = info.get("debtToEquity")
    roe = info.get("returnOnEquity")
    market_cap = info.get("marketCap")

    score = 50
    notes: list[str] = []
    if revenue_growth is not None:
        if revenue_growth > 0.15:
            score += 18; notes.append(f"Strong revenue growth: {pct(revenue_growth)}.")
        elif revenue_growth > 0:
            score += 8; notes.append(f"Positive revenue growth: {pct(revenue_growth)}.")
        else:
            score -= 12; notes.append(f"Negative/weak revenue growth: {pct(revenue_growth)}.")
    if profit_margin is not None:
        if profit_margin > 0.20:
            score += 15; notes.append(f"High profit margin: {pct(profit_margin)}.")
        elif profit_margin > 0.05:
            score += 5; notes.append(f"Moderate profit margin: {pct(profit_margin)}.")
        else:
            score -= 10; notes.append(f"Low profit margin: {pct(profit_margin)}.")
    if roe is not None:
        if roe > 0.20:
            score += 12; notes.append(f"Strong return on equity: {pct(roe)}.")
        elif roe > 0.05:
            score += 4; notes.append(f"Positive return on equity: {pct(roe)}.")
    if pe is not None:
        if pe < 25:
            score += 8; notes.append(f"Valuation looks reasonable by P/E: {pe:.1f}.")
        elif pe > 60:
            score -= 8; notes.append(f"Valuation is expensive by P/E: {pe:.1f}.")
    if debt_to_equity is not None:
        if debt_to_equity < 80:
            score += 5; notes.append("Debt/equity appears manageable.")
        elif debt_to_equity > 200:
            score -= 8; notes.append("Debt/equity appears elevated.")

    metrics = {
        "company": info.get("shortName", ticker),
        "sector": info.get("sector", "N/A"),
        "market_cap": market_cap,
        "pe": pe,
        "revenue_growth": revenue_growth,
        "profit_margin": profit_margin,
        "return_on_equity": roe,
        "debt_to_equity": debt_to_equity,
    }
    return FundamentalResult(
        ticker=ticker,
        score=clamp(score),
        metrics=metrics,
        notes=notes or ["Fundamental data was limited."],
        sources=[SourceLink("Yahoo Finance fundamentals", yahoo_quote_url(ticker) + "/key-statistics")],
    )
