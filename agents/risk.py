from __future__ import annotations

from app.models import RiskResult, SourceLink, TechnicalResult
from utils import clamp


def analyze_risk(ticker: str, technical: TechnicalResult, cash: float = 2000, risk_percent: float = 1.0) -> RiskResult:
    price = technical.price
    atr = max(technical.atr, price * 0.02)
    stop_loss = max(0.01, price - 2 * atr)
    take_profit = price + 3 * atr
    risk_per_share = max(0.01, price - stop_loss)
    risk_amount = cash * (risk_percent / 100)
    shares = int(risk_amount // risk_per_share)
    position_size = shares * price

    rr = (take_profit - price) / risk_per_share if risk_per_share else 0
    score = 50
    notes = []
    if rr >= 1.8:
        score += 20; notes.append("Risk/reward is attractive based on ATR target and stop.")
    else:
        score -= 15; notes.append("Risk/reward is not very attractive based on ATR target and stop.")
    if position_size <= cash * 0.35:
        score += 10; notes.append("Position size is controlled relative to available cash.")
    else:
        score -= 10; notes.append("Position size may be too large for the cash level.")
    if price <= technical.resistance * 0.98:
        score += 5; notes.append("Price is not extremely close to resistance.")
    else:
        score -= 8; notes.append("Price is close to resistance; entry risk is higher.")

    return RiskResult(
        ticker=ticker,
        score=clamp(score),
        stop_loss=stop_loss,
        take_profit=take_profit,
        position_size=position_size,
        shares=shares,
        risk_amount=risk_amount,
        notes=notes,
        sources=[
            SourceLink("ATR risk management reference", "https://www.investopedia.com/average-true-range-atr-4776277"),
            SourceLink("Position sizing reference", "https://www.investopedia.com/articles/trading/09/risk-management.asp"),
        ],
    )
