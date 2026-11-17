from pathlib import Path
from dataclasses import replace

import pytest

from agents.recovery import RecoveryCandidate
from app.monitor import MonitorAlert, format_portfolio_alert, format_ranked_alert, format_recovery_alert, materially_changed, run_monitor_once
from app.services import StockAnalysisResult
from data.portfolio import Holding


def _result(score: float = 76.0) -> StockAnalysisResult:
    return StockAnalysisResult("NVDA", 100.0, 80.0, 70.0, 60.0, 65.0, score, decision="Strong buy setup", notes=["Trend positive"], references={"Yahoo Finance": "https://example.com"})


def test_monitor_sends_initial_alert_and_saves_state(tmp_path: Path) -> None:
    sent = []
    changed = run_monitor_once(["NVDA"], state_path=tmp_path / "state.json", scanner=lambda **_: [_result()], notifier=lambda *args: sent.append(args))
    assert changed[0].signal == "Strong Buy"
    assert len(sent) == 1


def test_monitor_does_not_send_when_signal_is_unchanged(tmp_path: Path) -> None:
    state = tmp_path / "state.json"
    sent = []
    run_monitor_once(["NVDA"], state_path=state, scanner=lambda **_: [_result()], notifier=lambda *args: sent.append(args))
    changed = run_monitor_once(["NVDA"], state_path=state, scanner=lambda **_: [_result()], notifier=lambda *args: sent.append(args))
    assert changed == []
    assert len(sent) == 1


def test_material_change_detects_score_and_price_thresholds() -> None:
    alert = MonitorAlert("NVDA", 103.0, "Buy", 67.0, [], {})
    assert materially_changed(alert, {"price": 100, "score": 62, "signal": "Buy"})


def test_ranked_alert_groups_only_eligible_signals() -> None:
    alerts = [
        MonitorAlert("AAA", 100, "Strong Buy", 80, [], {}),
        MonitorAlert("BBB", 100, "Sell", 20, [], {}),
        MonitorAlert("CCC", 100, "Watch", 50, [], {}),
    ]
    message = format_ranked_alert(alerts, top_n=2)
    assert "Buy candidates (1)" in message
    assert "Watch / Hold (1)" in message
    assert "Sell candidates (1)" in message
    for ticker in ("AAA", "BBB", "CCC"):
        assert message.count(f"- {ticker}:") == 1


def test_delivered_report_separates_the_reported_four_symbols(tmp_path: Path) -> None:
    rows = [("MSFT", 517.99, 65.5), ("NVDA", 156.14, 54.7),
            ("QQQ", 661.75, 41.5), ("SPY", 739.95, 35.1)]
    results = [replace(_result(score), ticker=ticker, price=price)
               for ticker, price, score in rows]
    messages = []
    run_monitor_once([r.ticker for r in results], state_path=tmp_path / "state.json",
                     daily_report=True, rebound_top=0, scanner=lambda **_: results,
                     notifier=lambda _token, _chat, message: messages.append(message))
    message = messages[0]
    buy, rest = message.split("Watch / Hold (2)")
    neutral, sell = rest.split("Sell candidates (1)")
    assert "MSFT: Buy" in buy
    assert "NVDA: Watch" in neutral and "QQQ: Hold" in neutral
    assert "SPY: Sell" in sell
    assert "MSFT" not in sell and "NVDA" not in sell
    for ticker, _, _ in rows:
        assert message.count(f"- {ticker}:") == 1
    assert "Source: automated-stock-research-agent | report grouped-v2" in message
    assert "not calibrated probabilities" in message


def test_ranked_alert_does_not_force_buy_or_sell_candidates() -> None:
    message = format_ranked_alert([MonitorAlert("AAA", 100, "Hold", 40, [], {})])
    assert "Buy candidates (0)" in message
    assert "Sell candidates (0)" in message
    assert "No symbols currently meet the Buy / Strong Buy criteria" in message
    assert "No symbols currently meet the Sell / Strong Sell criteria" in message


def test_ranked_alert_sorts_and_caps_each_group() -> None:
    alerts = [MonitorAlert("BUY", 100, "Buy", 68, [], {}),
              MonitorAlert("STRONG", 100, "Strong Buy", 85, [], {}),
              MonitorAlert("SELL", 100, "Sell", 30, [], {}),
              MonitorAlert("WEAK", 100, "Strong Sell", 10, [], {})]
    message = format_ranked_alert(alerts, top_n=1)
    assert "- STRONG:" in message and "- WEAK:" in message
    assert "- BUY:" not in message and "- SELL:" not in message
    with pytest.raises(ValueError, match="at least 1"):
        format_ranked_alert(alerts, top_n=0)


def test_portfolio_alert_includes_holding_status_and_entry_context() -> None:
    message = format_portfolio_alert(
        [MonitorAlert("NVDA", 120, "Buy", 70, ["Technical: 80/100."], {})],
        [Holding("NVDA", "NVIDIA", "Stock", average_price=100)],
    )
    assert "NVDA (Stock): Buy" in message
    assert "vs average +20.0%" in message
    assert "Positive setup" in message


def test_recovery_alert_includes_horizon_and_review_levels() -> None:
    message = format_recovery_alert([
        RecoveryCandidate("AAA", 100, 70, "Stronger recovery watch", -4, "2–6 weeks; reassess weekly.", 90, 120, ["Five-day move: -4.0%.", "RSI is in a possible recovery zone."], "")
    ])
    assert "2–6 weeks" in message
    assert "Review risk" in message


def test_recovery_alert_handles_missing_levels_without_forecasting() -> None:
    message = format_recovery_alert([
        RecoveryCandidate("AAA", 100, 40, "High-risk recovery watch", -5,
                          "3-10 trading days", None, None,
                          ["Five-day move: -5.0%."], "")
    ])
    assert "No valid support-based risk review level" in message
    assert "No nearby resistance review level" in message
    assert "not predictions of recovery" in message
    assert "not probabilities" in message
