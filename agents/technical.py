from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD, ADXIndicator, EMAIndicator, SMAIndicator
from ta.volatility import AverageTrueRange, BollingerBands


@dataclass
class TechnicalAnalysis:
    ticker: str
    price: float
    score: float
    trend: str
    momentum: str
    signal: str
    rsi: float
    macd: float
    macd_signal: float
    sma20: float
    sma50: float
    ema20: float
    ema50: float
    atr: float
    adx: float
    support: float
    resistance: float
    notes: list[str]
    history: pd.DataFrame


def analyze_technical(ticker: str, history: pd.DataFrame) -> TechnicalAnalysis:
    df = history.copy()

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.dropna()

    close = df["Close"].squeeze()
    high = df["High"].squeeze()
    low = df["Low"].squeeze()

    df["SMA20"] = SMAIndicator(close, window=20).sma_indicator()
    df["SMA50"] = SMAIndicator(close, window=50).sma_indicator()
    df["EMA20"] = EMAIndicator(close, window=20).ema_indicator()
    df["EMA50"] = EMAIndicator(close, window=50).ema_indicator()
    df["RSI"] = RSIIndicator(close, window=14).rsi()

    macd_obj = MACD(close)
    df["MACD"] = macd_obj.macd()
    df["MACD_signal"] = macd_obj.macd_signal()

    bb = BollingerBands(close)
    df["BB_high"] = bb.bollinger_hband()
    df["BB_low"] = bb.bollinger_lband()

    atr_obj = AverageTrueRange(high=high, low=low, close=close)
    df["ATR"] = atr_obj.average_true_range()

    adx_obj = ADXIndicator(high=high, low=low, close=close)
    df["ADX"] = adx_obj.adx()

    df = df.dropna()

    latest = df.iloc[-1]

    price = float(latest["Close"])
    sma20 = float(latest["SMA20"])
    sma50 = float(latest["SMA50"])
    ema20 = float(latest["EMA20"])
    ema50 = float(latest["EMA50"])
    rsi = float(latest["RSI"])
    macd = float(latest["MACD"])
    macd_signal = float(latest["MACD_signal"])
    atr = float(latest["ATR"])
    adx = float(latest["ADX"])

    recent = df.tail(60)
    support = float(recent["Low"].min())
    resistance = float(recent["High"].max())

    score = 0
    notes: list[str] = []

    if price > sma50:
        score += 20
        notes.append("Price is above SMA50: medium-term trend is positive.")
    else:
        notes.append("Price is below SMA50: medium-term trend is weak.")

    if sma20 > sma50:
        score += 15
        notes.append("SMA20 is above SMA50: short-term trend confirms strength.")
    else:
        notes.append("SMA20 is below SMA50: trend confirmation is weak.")

    if ema20 > ema50:
        score += 10
        notes.append("EMA20 is above EMA50: momentum trend is positive.")
    else:
        notes.append("EMA20 is below EMA50: momentum trend is weak.")

    if 45 <= rsi <= 65:
        score += 15
        notes.append("RSI is in a healthy momentum zone.")
    elif rsi < 35:
        score += 8
        notes.append("RSI is low: possible oversold condition, but confirmation is needed.")
    elif rsi > 72:
        score -= 10
        notes.append("RSI is high: possible overbought risk.")
    else:
        notes.append("RSI is neutral.")

    if macd > macd_signal:
        score += 15
        notes.append("MACD is above signal line: bullish momentum.")
    else:
        notes.append("MACD is below signal line: momentum is not bullish.")

    if adx > 25:
        score += 10
        notes.append("ADX above 25: trend strength is meaningful.")
    else:
        notes.append("ADX below 25: trend strength is weak or unclear.")

    distance_to_resistance = ((resistance - price) / price) * 100
    distance_to_support = ((price - support) / price) * 100

    if distance_to_resistance > 8:
        score += 10
        notes.append("There is reasonable upside to recent resistance.")
    else:
        notes.append("Price is close to recent resistance; upside may be limited.")

    if distance_to_support < 4:
        score += 5
        notes.append("Price is near support; risk/reward may be interesting.")
    elif distance_to_support > 15:
        score -= 5
        notes.append("Price is far from support; pullback risk is higher.")

    score = max(0, min(100, score))

    if price > sma50 and sma20 > sma50:
        trend = "Bullish"
    elif price < sma50 and sma20 < sma50:
        trend = "Bearish"
    else:
        trend = "Mixed"

    if macd > macd_signal and 40 <= rsi <= 70:
        momentum = "Positive"
    elif macd < macd_signal and rsi < 50:
        momentum = "Weak"
    else:
        momentum = "Neutral"

    if score >= 75:
        signal = "BUY setup"
    elif score >= 55:
        signal = "WATCH"
    else:
        signal = "AVOID / WAIT"

    return TechnicalAnalysis(
        ticker=ticker.upper(),
        price=round(price, 2),
        score=round(score, 2),
        trend=trend,
        momentum=momentum,
        signal=signal,
        rsi=round(rsi, 2),
        macd=round(macd, 2),
        macd_signal=round(macd_signal, 2),
        sma20=round(sma20, 2),
        sma50=round(sma50, 2),
        ema20=round(ema20, 2),
        ema50=round(ema50, 2),
        atr=round(atr, 2),
        adx=round(adx, 2),
        support=round(support, 2),
        resistance=round(resistance, 2),
        notes=notes,
        history=df,
    )