from agents.technical import analyze_technical
import pytest

from providers.yahoo import get_market_data


def test_technical_analysis_with_real_data():
    try:
        market = get_market_data("NVDA", period="6mo")
    except (ValueError, OSError) as error:
        pytest.skip(f"Yahoo Finance is unavailable in this environment: {error}")
    technical = analyze_technical("NVDA", market.history)

    assert technical.ticker == "NVDA"
    assert technical.price > 0
    assert 0 <= technical.score <= 100
    assert technical.rsi > 0
    assert technical.support > 0
    assert technical.resistance > 0
    assert technical.signal in ["BUY setup", "WATCH", "AVOID / WAIT"]
