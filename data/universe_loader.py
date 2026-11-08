"""CSV-backed market-universe loading utilities.

The loader intentionally has no market-data dependency: the CSV is the source
of symbols and application services decide how to analyze them.
"""
from __future__ import annotations

import csv
import re
from collections.abc import Iterator, Sequence
from pathlib import Path


DEFAULT_UNIVERSE_PATH = Path(__file__).with_name("market_universe.csv")
REQUIRED_COLUMNS = {"symbol", "asset_type", "enabled"}
VALID_ASSET_TYPES = {"STOCK", "ETF"}
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9.\-^=]+$")


def load_market_universe(
    path: str | Path = DEFAULT_UNIVERSE_PATH,
    asset_types: Sequence[str] | None = None,
    limit: int | None = None,
) -> list[str]:
    """Return enabled, unique symbols from a universe CSV.

    The CSV must contain ``symbol``, ``asset_type``, and ``enabled`` columns.
    Blank, malformed, disabled, and unsupported rows are skipped, which makes
    the loader resilient to vendor exports containing delisted instruments.
    """
    if limit is not None and limit < 1:
        raise ValueError("limit must be at least 1 when provided")

    requested_types = _normalize_asset_types(asset_types)
    universe_path = Path(path)
    if not universe_path.exists():
        raise FileNotFoundError(f"Market universe CSV not found: {universe_path}")

    symbols: list[str] = []
    seen: set[str] = set()
    with universe_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = set(reader.fieldnames or ())
        missing_columns = REQUIRED_COLUMNS - fieldnames
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"Market universe CSV is missing required columns: {missing}")

        for row in reader:
            symbol = _normalize_symbol(row.get("symbol", ""))
            asset_type = row.get("asset_type", "").strip().upper()
            enabled = row.get("enabled", "").strip().lower()

            if (
                not symbol
                or asset_type not in requested_types
                or enabled not in {"1", "true", "yes", "y"}
                or symbol in seen
            ):
                continue

            seen.add(symbol)
            symbols.append(symbol)
            if limit is not None and len(symbols) >= limit:
                break

    return symbols


def iter_symbol_batches(symbols: Sequence[str], batch_size: int = 100) -> Iterator[list[str]]:
    """Yield symbol batches for rate-limited or scheduled scan workflows."""
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")

    for start in range(0, len(symbols), batch_size):
        yield list(symbols[start:start + batch_size])


def _normalize_asset_types(asset_types: Sequence[str] | None) -> set[str]:
    if asset_types is None:
        return VALID_ASSET_TYPES

    normalized = {asset_type.strip().upper() for asset_type in asset_types}
    invalid_types = normalized - VALID_ASSET_TYPES
    if invalid_types:
        invalid = ", ".join(sorted(invalid_types))
        raise ValueError(f"Unsupported asset types: {invalid}")
    return normalized


def _normalize_symbol(value: str) -> str | None:
    symbol = value.strip().upper()
    return symbol if SYMBOL_PATTERN.fullmatch(symbol) else None
