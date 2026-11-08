from __future__ import annotations

from dataclasses import dataclass

from agents.technical_agent import analyze_technical
from agents.fundamental_agent import analyze_fundamentals
from agents.news_agent import analyze_news
from agents.risk_agent import analyze_risk
from agents.cio_agent import make_decision


@dataclass
class ScanCandidate:
    ticker: str
    price: float
    final_score: float
    decision: str
    technical: int
    fundamentals: int
    news: int
    risk: int
    notes: str


def scan_watchlist(watchlist: list[str], cash: float, risk_percent: float, top: int = 5) -> list[ScanCandidate]:
    candidates: list[ScanCandidate] = []
    for ticker in watchlist:
        ticker = ticker.strip().upper()
        if not ticker:
            continue
        try:
            technical = analyze_technical(ticker)
            fundamentals = analyze_fundamentals(ticker)
            news = analyze_news(ticker)
            risk = analyze_risk(ticker, technical, cash=cash, risk_percent=risk_percent)
            decision = make_decision(ticker, technical, fundamentals, news, risk)
            candidates.append(
                ScanCandidate(
                    ticker=ticker,
                    price=technical.price,
                    final_score=decision.final_score,
                    decision=decision.decision,
                    technical=technical.score,
                    fundamentals=fundamentals.score,
                    news=news.score,
                    risk=risk.score,
                    notes=" | ".join(decision.reasons[:2]),
                )
            )
        except Exception as exc:
            candidates.append(ScanCandidate(ticker, 0, 0, f"Error: {exc}", 0, 0, 0, 0, ""))
    candidates.sort(key=lambda x: x.final_score, reverse=True)
    return candidates[:top]
