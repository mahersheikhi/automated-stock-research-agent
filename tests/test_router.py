from app.router import parse
from app.router_models import Intent


def test_scan():
    req = parse("What should I buy today?")
    assert req.intent == Intent.SCAN


def test_analyze():
    req = parse("Analyze NVDA")
    assert req.intent == Intent.ANALYZE
    assert req.tickers == ["NVDA"]


def test_compare():
    req = parse("Compare NVDA and AMD")
    assert req.intent == Intent.COMPARE