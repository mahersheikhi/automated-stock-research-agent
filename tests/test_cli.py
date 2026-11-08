from app.cli import build_parser


def test_analyze_command() -> None:
    parser = build_parser()

    args = parser.parse_args(
        ["analyze", "NVDA", "--cash", "2000", "--risk", "1"]
    )

    assert args.command == "analyze"
    assert args.ticker == "NVDA"
    assert args.cash == 2000
    assert args.risk == 1


def test_scan_command() -> None:
    parser = build_parser()

    args = parser.parse_args(
        ["scan", "--tickers", "NVDA,AVGO", "--top", "2"]
    )

    assert args.command == "scan"
    assert args.tickers == "NVDA,AVGO"
    assert args.top == 2


def test_monitor_command() -> None:
    args = build_parser().parse_args(["monitor", "--tickers", "NVDA,AVGO", "--interval-minutes", "30", "--no-send"])
    assert args.command == "monitor"
    assert args.interval_minutes == 30
    assert args.no_send is True


def test_monitor_universe_and_daily_report_options() -> None:
    args = build_parser().parse_args(["monitor", "--universe", "--daily-report"])
    assert args.universe is True
    assert args.daily_report is True
