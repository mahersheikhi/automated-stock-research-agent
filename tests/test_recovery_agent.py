from types import SimpleNamespace

from agents.recovery import evaluate_recovery


def test_recovery_agent_ranks_constructive_pullback() -> None:
    result = SimpleNamespace(
        ticker="AAA", price=100.0, final_score=70.0, five_day_change=-5.0,
        rsi=38.0, support=96.0, macd=2.0, macd_signal=1.0,
        news_score=70.0, trend="Mixed", atr=3.0, resistance=120.0,
        references={"Yahoo Finance": "https://example.com"},
    )
    candidate = evaluate_recovery(result)
    assert candidate is not None
    assert candidate.score >= 70
    assert candidate.risk_review_price == 94.5
