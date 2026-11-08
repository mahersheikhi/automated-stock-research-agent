from __future__ import annotations

from dataclasses import dataclass
import logging
from collections.abc import Sequence
from typing import Any

from agents.news import analyze_news
from agents.technical import analyze_technical
from agents.fundamental import analyze_fundamentals
from agents.risk import analyze_risk
from agents.recovery import RecoveryCandidate, evaluate_recovery
from app.models import TechnicalResult
from data.universe_loader import load_market_universe
from providers.yahoo import get_market_data


logger = logging.getLogger(__name__)

@dataclass
class StockAnalysisResult:
    ticker: str
    price: float

    technical_score: float
    fundamental_score: float
    risk_score: float

    news_score: float | None = None

    final_score: float = 0.0
    confidence: int = 100

    decision: str = ""

    is_eligible: bool = False

    entry_price: float | None = None
    stop_loss: float | None = None
    target1: float | None = None
    target2: float |None = None

    news_available: bool = True
    news_article_count: int = 0
    news_summary: str = ""
    news_sentiment: str = ""

    notes: list[str] | None = None
    references: dict[str, str] | None = None
    trend: str = "Unknown"
    momentum: str = "Unknown"
    rsi: float = 0.0
    macd: float = 0.0
    macd_signal: float = 0.0
    atr: float = 0.0
    support: float = 0.0
    resistance: float = 0.0
    five_day_change: float | None = None
    
def analyze_stock(
    ticker: str,
    cash: float = 2000,
    risk_percent: float = 1,
) -> StockAnalysisResult:
    ticker = ticker.upper()

    market = get_market_data(ticker)
    technical = analyze_technical(ticker=ticker, history=market.history)

    price = technical.price
    five_day_change: float | None = None
    try:
        close = technical.history["Close"].dropna()
        if len(close) >= 6:
            five_day_change = ((float(close.iloc[-1]) / float(close.iloc[-6])) - 1) * 100
    except (AttributeError, KeyError, TypeError, IndexError):
        pass

    entry_price = round(price, 2)

    stop_loss = round(price * 0.95, 2)

    target1 = round(price * 1.08, 2)

    target2 = round(price * 1.15, 2)
    technical_score = technical.score

    fundamentals = analyze_fundamentals(ticker)
    fundamental_score = fundamentals.score
    confidence: int = 100
    news_available: bool = True
    news_article_count: int = 0
    news_summary: str = ""
    news_sentiment: str = ""

    try:
        news = analyze_news(ticker)

        if news.article_count > 0:
            news_score = news.score
            news_sentiment = news.sentiment
            news_summary = news.summary
            news_article_count = news.article_count
            news_available = True
        else:
            news_score = None
            news_sentiment = "Unavailable"
            news_summary = "No recent news found."
            news_article_count = 0
            news_available = False
            confidence -= 20

    except Exception as error:
        logger.warning("News analysis unavailable for %s: %s", ticker, error)

        news_score = None
        news_sentiment = "Unavailable"
        news_summary = "News service unavailable."
        news_article_count = 0
        news_available = False
        confidence -= 20

    
    # Adapt the established technical result to the risk agent's shared model.
    risk_technical = TechnicalResult(
        ticker=ticker, price=price, score=technical.score, trend=technical.trend,
        momentum=technical.momentum, rsi=technical.rsi, macd=technical.macd,
        macd_signal=technical.macd_signal, sma20=technical.sma20, sma50=technical.sma50,
        atr=technical.atr, adx=technical.adx, support=technical.support,
        resistance=technical.resistance, notes=technical.notes, sources=[],
    )
    risk = analyze_risk(ticker, risk_technical, cash=cash, risk_percent=risk_percent)
    risk_score = risk.score

    score = 0
    weight = 0

    score += technical_score * 0.40
    weight += 0.40

    score += fundamental_score * 0.30
    weight += 0.30

    score += risk_score * 0.15
    weight += 0.15

    if news_score is not None:
        score += news_score * 0.15
        weight += 0.15

    final_score = score / weight

    decision = _classify_opportunity(
        final_score=final_score,
        technical_score=technical.score,
        trend=technical.trend,
        momentum=technical.momentum,
    )

    return StockAnalysisResult(
        confidence=confidence,

        news_available=news_available,
        news_article_count=news_article_count,
        news_summary=news_summary,
        news_sentiment=news_sentiment,
        ticker=ticker,

        price=price,

        technical_score=technical_score,
        fundamental_score=fundamental_score,
        news_score=news_score,
        risk_score=risk_score,

        final_score=round(final_score,2),

        decision=decision,

        entry_price=entry_price,
        stop_loss=stop_loss,
        target1=target1,
        target2=target2,

        notes=[
            *technical.notes[:2],
            *fundamentals.notes[:1],
            *risk.notes[:1],
            f"News sentiment: {news_sentiment}.",
        ],

        references={
            "Yahoo Finance": f"https://finance.yahoo.com/quote/{ticker}",
            "Google News": f"https://news.google.com/search?q={ticker}",
            **{source.name: source.url for source in fundamentals.sources + risk.sources},
        },
        trend=technical.trend,
        momentum=technical.momentum,
        rsi=technical.rsi,
        macd=technical.macd,
        macd_signal=technical.macd_signal,
        atr=technical.atr,
        support=technical.support,
        resistance=technical.resistance,
        five_day_change=round(five_day_change, 2) if five_day_change is not None else None,
    )


def scan_recovery_candidates(
    tickers: Sequence[str],
    cash: float = 2000,
    risk_percent: float = 1,
    top_n: int = 5,
) -> list[RecoveryCandidate]:
    """Rank recent pullbacks with technical and news evidence for further research."""
    candidates: list[RecoveryCandidate] = []
    for ticker in dict.fromkeys(ticker.strip().upper() for ticker in tickers if ticker and ticker.strip()):
        try:
            candidate = evaluate_recovery(analyze_stock(ticker, cash, risk_percent))
            if candidate is not None:
                candidates.append(candidate)
        except Exception as error:
            logger.warning("Skipping %s during recovery scan: %s", ticker, error)
    return sorted(candidates, key=lambda candidate: candidate.score, reverse=True)[:top_n]

def scan_sell_candidates(
    tickers: list[str],
    cash: float = 2000,
    risk_percent: float = 1,
    top_n: int = 5,
) -> list[StockAnalysisResult]:
    """
    Scan a watchlist for stocks showing potential sell/reduce-risk conditions.

    This is an analytical signal, not financial advice.
    """

    results = []

    for ticker in tickers:
        try:
            result = analyze_stock(
                ticker=ticker,
                cash=cash,
                risk_percent=risk_percent,
            )

            # Sell pressure score:
            # Higher = more evidence of deterioration.
            sell_score = 100 - result.final_score

            # Stronger sell classification when overall score is weak.
            if sell_score >= 70:
                result.decision = "SELL / reduce risk"
            elif sell_score >= 55:
                result.decision = "SELL WATCH"
            else:
                result.decision = "HOLD"

            result.notes = (result.notes or []) + [
                f"Sell-pressure score: {sell_score:.1f}/100"
            ]

            # Temporarily attach score for sorting.
            result._sell_score = sell_score

            results.append(result)

        except Exception as exc:
            print(f"Could not analyze {ticker}: {exc}")

    results.sort(
        key=lambda x: getattr(x, "_sell_score", 0),
        reverse=True,
    )

    return results[:top_n]

def _classify_opportunity(
    *,
    final_score: float,
    technical_score: float,
    trend: str,
    momentum: str,
) -> str:
    """Translate the weighted score into an explainable, attainable setup label.

    Fundamentals and risk are currently neutral placeholders (50/100). News is
    scored from recent headlines, so the thresholds allow modest confirmation
    without letting it override the technical setup.
    """
    if (
        final_score >= 59
        and technical_score >= 75
        and trend == "Bullish"
        and momentum == "Positive"
    ):
        decision = "Strong buy setup"
    elif final_score >= 54 and technical_score >= 60 and trend != "Bearish":
        decision = "Possible buy"
    elif final_score >= 46:
        decision = "Watch"
    else:
        decision = "Avoid for now"

    return decision


def scan_market(
    tickers: Sequence[str] | None = None,
    cash: float = 2000,
    risk_percent: float = 1,
    top_n: int = 5,
    minimum_score: float = 0,
    asset_types: Sequence[str] | None = None,
    universe_limit: int | None = None,
) -> list[StockAnalysisResult]:
    """Analyze and rank the best available opportunities in a market universe.

    A scan never filters on a decision label: it returns the strongest valid
    candidates, including ``Watch`` setups when market conditions are weak.
    """
    if top_n < 1:
        raise ValueError("top_n must be at least 1")

    candidates = (
        tickers
        if tickers is not None
        else load_market_universe(asset_types=asset_types, limit=universe_limit)
    )
    normalized_tickers = list(dict.fromkeys(
        ticker.strip().upper() for ticker in candidates if ticker and ticker.strip()
    ))
    results: list[StockAnalysisResult] = []

    for ticker in normalized_tickers:
        try:
            result = analyze_stock(
                ticker=ticker,
                cash=cash,
                risk_percent=risk_percent,
            )
            if result.final_score >= minimum_score:
                results.append(result)
        except Exception as error:
            logger.warning("Skipping %s during market scan: %s", ticker, error)
    
    
    ranked = sorted(
        results,
        key=lambda result: (result.final_score, result.technical_score),
        reverse=True,
    )
    return ranked[:top_n]

def answer_question(
    question: str,
    tickers: list[str] | None = None,
    cash: float = 2000,
    risk_percent: float = 1,
) -> Any:
    question_lower = question.lower()

    if tickers is None:
        tickers = load_market_universe()

    if "buy today" in question_lower or "what should i buy" in question_lower:
        return scan_market(
            tickers=tickers,
            cash=cash,
            risk_percent=risk_percent,
        )

    if (
    "sell today" in question_lower
    or "what should i sell" in question_lower
    or "which stocks should i sell" in question_lower):
      return scan_sell_candidates(
        tickers=tickers,
        cash=cash,
        risk_percent=risk,
       )
    
    if "analyze" in question_lower:
        words = question.upper().split()
        ticker = words[-1]
        return analyze_stock(
            ticker=ticker,
            cash=cash,
            risk_percent=risk_percent,
        )

    return {
    "answer": "I can currently answer: 'What should I buy today?' or 'Analyze NVDA'."
    }
