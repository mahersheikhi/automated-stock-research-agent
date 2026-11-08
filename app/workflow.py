from app.router_models import Intent
from app.router import parse
from app.services import analyze_stock, scan_market


DEFAULT_SCAN = [
    "NVDA",
    "AVGO",
    "MSFT",
    "META",
    "AMZN",
    "TSM",
    "ASML",
    "RHM.DE",
]


def execute(question: str):
    request = parse(question)

    if request.intent == Intent.SCAN:
        return scan_market(DEFAULT_SCAN)

    if request.intent == Intent.ANALYZE:
        if request.tickers:
            return analyze_stock(request.tickers[0])

    return {
        "message": "I don't understand yet."
    }