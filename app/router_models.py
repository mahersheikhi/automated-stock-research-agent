from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Intent(str, Enum):
    ANALYZE = "analyze"
    SCAN = "scan"
    COMPARE = "compare"
    PORTFOLIO = "portfolio"
    NEWS = "news"
    HELP = "help"


@dataclass(frozen=True)
class RouterRequest:
    question: str
    intent: Intent
    tickers: list[str]