from pathlib import Path

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


def test_ranked_alert_lists_strongest_and_weakest_candidates() -> None:
    alerts = [
        MonitorAlert("AAA", 100, "Strong Buy", 80, [], {}),
        MonitorAlert("BBB", 100, "Sell", 20, [], {}),
        MonitorAlert("CCC", 100, "Watch", 50, [], {}),
    ]
    message = format_ranked_alert(alerts, top_n=2)
    assert "Top 2 buy candidates" in message
    assert message.index("AAA") < message.index("CCC")
    assert message.index("BBB") > message.index("Top 2 sell candidates")


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
