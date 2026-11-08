from __future__ import annotations

import math
from typing import Any


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if hasattr(value, "iloc"):
            value = value.iloc[0]
        out = float(value)
        if math.isnan(out) or math.isinf(out):
            return default
        return out
    except Exception:
        return default


def clamp(value: float, low: float = 0, high: float = 100) -> int:
    return int(max(low, min(high, round(value))))


def pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    try:
        return f"{float(value) * 100:.1f}%"
    except Exception:
        return "N/A"


def money(value: float | None) -> str:
    if value is None:
        return "N/A"
    try:
        return f"{float(value):,.2f}"
    except Exception:
        return "N/A"
