from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd
import yfinance as yf

from dataclasses import dataclass


@dataclass
class MarketData:
    ticker: str
    price: float
    history: pd.DataFrame
    references: dict[str, str]


def get_market_data(ticker: str, period: str = "1y") -> MarketData:
    ticker = ticker.upper()
    quote = get_live_quote(ticker)
    history = get_price_history(ticker, period=period)

    return MarketData(
        ticker=ticker,
        price=float(quote["price"]),
        history=history,
        references={
            "Yahoo Finance Quote": yahoo_quote_url(ticker),
            "Yahoo Finance History": yahoo_history_url(ticker),
        },
    )

def _flatten_yfinance_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Handle yfinance MultiIndex columns returned by newer versions."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def get_price_history(ticker: str, period: str = "1y", interval: str = "1d", auto_adjust: bool = True) -> pd.DataFrame:
    """
    Historical data for technical indicators and charts.

    Note: This is not used as the displayed current quote because historical daily
    data can lag the live Yahoo quote and can be adjusted for dividends/splits.
    """
    df = yf.download(ticker, period=period, interval=interval, auto_adjust=auto_adjust, progress=False)
    if df.empty:
        raise ValueError(f"No price data found for {ticker}")
    df = _flatten_yfinance_columns(df)
    df = df.dropna(how="all")
    return df


def get_ticker_info(ticker: str) -> dict[str, Any]:
    try:
        return yf.Ticker(ticker).info or {}
    except Exception:
        return {}


def get_live_quote(ticker: str) -> dict[str, Any]:
    """
    Get the displayed quote price from Yahoo's quote endpoint via yfinance.

    Priority:
    1) fast_info.last_price, which is usually closest to the Yahoo quote page.
    2) regularMarketPrice from info.
    3) currentPrice from info.
    4) fallback to latest non-adjusted historical close.

    This prevents the report from showing an adjusted historical close as the
    current price.
    """
    t = yf.Ticker(ticker)
    currency = None
    exchange = None
    quote_source = "Yahoo Finance quote"
    price = None

    try:
        fast = t.fast_info
        # fast_info behaves like a dict in recent yfinance versions, but can also
        # expose attributes depending on version.
        if hasattr(fast, "get"):
            price = fast.get("last_price") or fast.get("regular_market_price") or fast.get("lastPrice")
            currency = fast.get("currency")
            exchange = fast.get("exchange")
        else:
            price = getattr(fast, "last_price", None) or getattr(fast, "regular_market_price", None)
            currency = getattr(fast, "currency", None)
            exchange = getattr(fast, "exchange", None)
    except Exception:
        pass

    if price is None:
        info = get_ticker_info(ticker)
        price = info.get("regularMarketPrice") or info.get("currentPrice") or info.get("previousClose")
        currency = currency or info.get("currency") or info.get("financialCurrency")
        exchange = exchange or info.get("exchange") or info.get("fullExchangeName")

    if price is None:
        # Non-adjusted close is a better fallback for matching Yahoo than
        # auto-adjusted close.
        hist = get_price_history(ticker, period="5d", interval="1d", auto_adjust=False)
        price = hist["Close"].dropna().iloc[-1]
        quote_source = "Yahoo Finance historical close fallback"

    return {
        "price": float(price),
        "currency": currency or "",
        "exchange": exchange or "",
        "source": quote_source,
        "retrieved_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "url": yahoo_quote_url(ticker),
    }


def yahoo_quote_url(ticker: str) -> str:
    return f"https://finance.yahoo.com/quote/{ticker}"


def yahoo_history_url(ticker: str) -> str:
    return f"https://finance.yahoo.com/quote/{ticker}/history"
