from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt


def create_price_chart(ticker: str, history, output_dir: str = "reports") -> str:
    """Create a price chart with moving averages and educational buy/watch/sell markers."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    path = Path(output_dir) / f"{ticker}_chart.png"

    df = history.copy().dropna()

    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(df.index, df["Close"], label="Close")

    if "SMA20" in df.columns:
        ax.plot(df.index, df["SMA20"], label="SMA20")

    if "SMA50" in df.columns:
        ax.plot(df.index, df["SMA50"], label="SMA50")

    required_cols = {"Close", "SMA20", "SMA50", "RSI", "MACD", "MACD_signal"}

    if required_cols.issubset(df.columns):
        signal_df = df.tail(60).copy()

        buy_signals = signal_df[
            (signal_df["Close"] > signal_df["SMA50"]) &
            (signal_df["RSI"] > 40) &
            (signal_df["RSI"] < 65) &
            (signal_df["MACD"] > signal_df["MACD_signal"])
        ]

        watch_signals = signal_df[
            (signal_df["Close"] > signal_df["SMA20"]) &
            (signal_df["RSI"] >= 35) &
            (signal_df["RSI"] <= 70)
        ]

        sell_signals = signal_df[
            (signal_df["RSI"] > 72) |
            (
                (signal_df["Close"] < signal_df["SMA20"]) &
                (signal_df["MACD"] < signal_df["MACD_signal"])
            )
        ]

        if not buy_signals.empty:
            ax.scatter(
                buy_signals.index,
                buy_signals["Close"],
                marker="^",
                s=120,
                label="BUY setup",
                zorder=5,
            )

        if not watch_signals.empty:
            ax.scatter(
                watch_signals.index,
                watch_signals["Close"],
                marker="o",
                s=45,
                label="WATCH / possible entry",
                zorder=4,
            )

        if not sell_signals.empty:
            ax.scatter(
                sell_signals.index,
                sell_signals["Close"],
                marker="v",
                s=120,
                label="SELL / reduce risk",
                zorder=5,
            )

    ax.set_title(f"{ticker} price chart with buy/watch/sell setup markers")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    ax.legend()
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)

    return str(path)