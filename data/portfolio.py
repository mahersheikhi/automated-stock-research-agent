"""Local, non-secret portfolio configuration for monitor summaries."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


DEFAULT_PORTFOLIO_PATH = Path("config/portfolio.json")


@dataclass(frozen=True)
class Holding:
    ticker: str
    name: str
    asset_type: str
    average_price: float | None = None
    units: float | None = None


def load_portfolio(path: str | Path = DEFAULT_PORTFOLIO_PATH) -> list[Holding]:
    """Load a user-maintained portfolio file without storing broker credentials."""
    portfolio_path = Path(path)
    if not portfolio_path.exists():
        return []

    raw = json.loads(portfolio_path.read_text(encoding="utf-8"))
    holdings: list[Holding] = []
    for item in raw.get("holdings", []):
        ticker = str(item.get("ticker", "")).strip().upper()
        if not ticker:
            continue
        holdings.append(
            Holding(
                ticker=ticker,
                name=str(item.get("name", ticker)),
                asset_type=str(item.get("asset_type", "Stock")),
                average_price=_optional_float(item.get("average_price")),
                units=_optional_float(item.get("units")),
            )
        )
    return holdings


def _optional_float(value: object) -> float | None:
    return float(value) if value is not None else None
