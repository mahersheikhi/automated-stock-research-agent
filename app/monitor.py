"""Stateful watchlist monitoring and Telegram-ready alert formatting."""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Sequence

from app.services import StockAnalysisResult, scan_market, scan_recovery_candidates
from agents.recovery import RecoveryCandidate, evaluate_recovery
from config.settings import settings
from data.portfolio import Holding
from providers.telegram import send_telegram_message


DEFAULT_STATE_PATH = Path("data/monitor_state.json")


@dataclass(frozen=True)
class MonitorAlert:
    ticker: str
    price: float
    signal: str
    score: float
    reasons: list[str]
    references: dict[str, str]


def signal_for(result: StockAnalysisResult) -> str:
    """Convert the existing combined score into neutral research-signal labels."""
    score = result.final_score
    if score >= 75:
        return "Strong Buy"
    if score >= 62:
        return "Buy"
    if score >= 50:
        return "Watch"
    if score >= 38:
        return "Hold"
    if score >= 25:
        return "Sell"
    return "Strong Sell"


def _reasons(result: StockAnalysisResult) -> list[str]:
    notes = (result.notes or [])[:3]
    news = f"News: {result.news_sentiment or 'Unavailable'} ({result.news_score if result.news_score is not None else 'n/a'}/100)."
    return [f"Technical: {result.technical_score:.0f}/100.", news, *notes][:4]


def build_alert(result: StockAnalysisResult) -> MonitorAlert:
    return MonitorAlert(
        ticker=result.ticker,
        price=result.price,
        signal=signal_for(result),
        score=result.final_score,
        reasons=_reasons(result),
        references=result.references or {},
    )


def load_state(path: Path = DEFAULT_STATE_PATH) -> dict[str, dict]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_state(state: dict[str, dict], path: Path = DEFAULT_STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def materially_changed(alert: MonitorAlert, previous: dict | None) -> bool:
    """Alert on a label shift, a five-point score move, or a three-percent move."""
    if previous is None:
        return True
    old_price = float(previous.get("price", 0))
    price_change = abs(alert.price - old_price) / old_price if old_price else 1.0
    return (
        alert.signal != previous.get("signal")
        or abs(alert.score - float(previous.get("score", alert.score))) >= 5
        or price_change >= 0.03
    )


def format_alert(alerts: Sequence[MonitorAlert]) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"Market monitor — {timestamp}", "Research signals only; not investment advice."]
    for alert in alerts:
        lines += ["", f"{alert.ticker}: {alert.signal} | ${alert.price:,.2f} | score {alert.score:.1f}/100"]
        lines.extend(f"- {reason}" for reason in alert.reasons)
        lines.extend(f"{name}: {url}" for name, url in alert.references.items())
    return "\n".join(lines)


def format_ranked_alert(alerts: Sequence[MonitorAlert], top_n: int = 5) -> str:
    """Format the strongest and weakest research signals as separate rankings."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    strongest = sorted(alerts, key=lambda alert: alert.score, reverse=True)[:top_n]
    weakest = sorted(alerts, key=lambda alert: alert.score)[:top_n]
    lines = [
        f"Daily market monitor — {timestamp}",
        "Research signals only; not investment advice.",
        "",
        f"Top {len(strongest)} buy candidates",
    ]
    for alert in strongest:
        lines.append(f"- {alert.ticker}: {alert.signal} | ${alert.price:,.2f} | {alert.score:.1f}/100")
    lines += ["", f"Top {len(weakest)} sell candidates"]
    for alert in weakest:
        lines.append(f"- {alert.ticker}: {alert.signal} | ${alert.price:,.2f} | {alert.score:.1f}/100")
    lines += ["", "Sources: Yahoo Finance and Google News links are available in the detailed local monitor output."]
    return "\n".join(lines)


def holding_status(alert: MonitorAlert) -> str:
    """Plain-language research status for an existing holding, not trade advice."""
    if alert.signal in {"Strong Buy", "Buy"}:
        return "Positive setup — keep under review; adding needs your own risk check."
    if alert.signal == "Watch":
        return "Mixed setup — keep and watch for technical confirmation."
    if alert.signal == "Hold":
        return "Neutral/weak setup — review against your allocation and risk plan."
    if alert.signal == "Sell":
        return "Weak setup — review promptly and consider a risk-reduction plan."
    return "High caution — review promptly before making any decision."


def format_portfolio_alert(alerts: Sequence[MonitorAlert], holdings: Sequence[Holding]) -> str:
    """Create a compact daily summary for every configured portfolio holding."""
    by_ticker = {alert.ticker: alert for alert in alerts}
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"Portfolio check — {timestamp}", "Research signals only; not investment advice."]
    for holding in holdings:
        alert = by_ticker.get(holding.ticker)
        if alert is None:
            lines += ["", f"{holding.ticker}: Data unavailable today — no conclusion."]
            continue
        entry_context = ""
        if holding.average_price:
            change = ((alert.price - holding.average_price) / holding.average_price) * 100
            entry_context = f" | vs average {change:+.1f}%"
        reason = alert.reasons[0] if alert.reasons else "Technical and news signals reviewed."
        lines += [
            "",
            f"{holding.ticker} ({holding.asset_type}): {alert.signal} | price {alert.price:,.2f} | score {alert.score:.1f}/100{entry_context}",
            f"- {holding_status(alert)}",
            f"- {reason}",
        ]
    return "\n".join(lines)


def format_recovery_alert(candidates: Sequence[RecoveryCandidate]) -> str:
    lines = ["Pullback recovery candidates", "Research signals only; not buy or sell instructions."]
    if not candidates:
        return "\n".join([*lines, "No recent pullbacks met the recovery-watch criteria today."])
    for candidate in candidates:
        lines += [
            "",
            f"{candidate.ticker}: {candidate.label} | price {candidate.price:,.2f} | recovery score {candidate.score:.1f}/100",
            f"- Pullback: {candidate.five_day_change:.1f}% in five trading days. {candidate.horizon}",
            f"- Review risk if a daily close is below {candidate.risk_review_price:,.2f}; reassess near {candidate.target_review_price:,.2f}.",
            f"- {candidate.reasons[1] if len(candidate.reasons) > 1 else candidate.reasons[0]}",
        ]
    return "\n".join(lines)


def run_monitor_once(
    tickers: Sequence[str],
    *,
    cash: float = 2000,
    risk_percent: float = 1,
    state_path: Path = DEFAULT_STATE_PATH,
    send: bool = True,
    daily_report: bool = False,
    top_n: int = 5,
    rebound_top: int = 5,
    portfolio: Sequence[Holding] | None = None,
    scanner: Callable[..., list[StockAnalysisResult]] = scan_market,
    notifier: Callable[[str, str, str], None] = send_telegram_message,
) -> list[MonitorAlert]:
    """Scan a watchlist, persist observed signals, and notify only meaningful changes."""
    results = scanner(tickers=tickers, cash=cash, risk_percent=risk_percent, top_n=len(tickers))
    alerts = [build_alert(result) for result in results]
    old_state = load_state(state_path)
    changed = [alert for alert in alerts if materially_changed(alert, old_state.get(alert.ticker))]
    save_state({alert.ticker: asdict(alert) for alert in alerts}, state_path)
    if send and (changed or daily_report):
        if portfolio:
            message = format_portfolio_alert(alerts, portfolio)
            if daily_report:
                message = f"{message}\n\n{format_ranked_alert(alerts, top_n)}"
        else:
            message = format_ranked_alert(alerts, top_n) if daily_report else format_alert(changed)
        if daily_report and rebound_top > 0:
            recovery = sorted(
                (candidate for result in results
                 if (candidate := evaluate_recovery(result)) is not None),
                key=lambda candidate: candidate.score,
                reverse=True,
            )[:rebound_top]
            message = f"{message}\n\n{format_recovery_alert(recovery)}"
        notifier(settings.telegram_bot_token, settings.telegram_chat_id, message)
    return changed


def run_continuously(tickers: Sequence[str], interval_minutes: float, **kwargs) -> None:
    if interval_minutes <= 0:
        raise ValueError("interval_minutes must be greater than zero")
    while True:
        changed = run_monitor_once(tickers, **kwargs)
        print(f"Monitor checked {len(tickers)} ticker(s); {len(changed)} material change(s).")
        time.sleep(interval_minutes * 60)
