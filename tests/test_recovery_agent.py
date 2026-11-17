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


def _pullback(**overrides):
    values = dict(ticker="NVDA", price=168.89, final_score=52.2,
                  five_day_change=-18.3, rsi=28, support=164.27,
                  macd=-8, macd_signal=-6, news_score=30,
                  trend="Bearish", atr=5.46, resistance=243.37, references={})
    values.update(overrides)
    return SimpleNamespace(**values)


def test_distant_high_is_not_a_short_term_recovery_target() -> None:
    candidate = evaluate_recovery(_pullback())
    assert candidate.target_review_price is None
    assert candidate.risk_review_price == 161.54


def test_nearby_resistance_is_retained_as_an_observation_level() -> None:
    candidate = evaluate_recovery(_pullback(resistance=178.67))
    assert candidate.target_review_price == 178.67


def test_broken_support_does_not_earn_a_proximity_bonus() -> None:
    broken = evaluate_recovery(_pullback(support=180))
    absent = evaluate_recovery(_pullback(support=0))
    assert broken.score == absent.score
    assert broken.risk_review_price is None


def test_missing_volatility_does_not_invent_review_levels() -> None:
    for atr in (0, -1, float("nan"), float("inf")):
        candidate = evaluate_recovery(_pullback(atr=atr))
        assert candidate.risk_review_price is None
        assert candidate.target_review_price is None
