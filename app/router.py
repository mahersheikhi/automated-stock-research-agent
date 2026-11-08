from __future__ import annotations

import re

from app.router_models import Intent, RouterRequest


TICKER_REGEX = r"\b[A-Z]{1,5}(?:\.DE)?\b"


def detect_intent(question: str) -> Intent:
    q = question.lower()

    if "buy today" in q:
        return Intent.SCAN

    if "compare" in q:
        return Intent.COMPARE

    if "portfolio" in q:
        return Intent.PORTFOLIO

    if "news" in q:
        return Intent.NEWS

    if "analyze" in q or "buy" in q:
        return Intent.ANALYZE

    return Intent.HELP


def extract_tickers(question: str) -> list[str]:
    return re.findall(TICKER_REGEX, question.upper())


def parse(question: str) -> RouterRequest:
    return RouterRequest(
        question=question,
        intent=detect_intent(question),
        tickers=extract_tickers(question),
    )