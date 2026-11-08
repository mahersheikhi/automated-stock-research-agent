from __future__ import annotations

import argparse
from dataclasses import asdict, is_dataclass
from typing import Any

from app.services import analyze_stock, scan_market, scan_sell_candidates
from app.monitor import run_continuously, run_monitor_once
from data.universe_loader import load_market_universe
from data.portfolio import load_portfolio


DEFAULT_SCAN_TICKERS: list[str] = []


def print_result(result: Any) -> None:
    """Print dataclasses, dictionaries, or lists in a readable CLI format."""

    if isinstance(result, list):
        if not result:
            print("No results found.")
            return

        print("\nRanked candidates")
        print("=" * 78)

        for rank, item in enumerate(result, start=1):
            data = asdict(item) if is_dataclass(item) else item

            print(
                f"{rank:>2}. {data['ticker']:<10} "
                f"Price: {data['price']:<10.2f} "
                f"Score: {data['final_score']:<6.2f} "
                f"Decision: {data['decision']}"
            )

        return

    data = asdict(result) if is_dataclass(result) else result

    if not isinstance(data, dict):
        print(data)
        return

    print("\nStock analysis")
    print("=" * 60)

    for key, value in data.items():
        if key == "notes":
            print("\nNotes:")
            for note in value:
                print(f"  - {note}")

        elif key == "references":
            print("\nReferences:")
            for name, url in value.items():
                print(f"  - {name}: {url}")

        else:
            label = key.replace("_", " ").title()
            print(f"{label}: {value}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stock-assistant",
        description="AI Stock Research Assistant CLI",
    )

    subparsers = parser.add_subparsers(dest="command")

    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze one stock",
    )
    analyze_parser.add_argument(
        "ticker",
        help="Yahoo Finance ticker, for example NVDA or RHM.DE",
    )
    analyze_parser.add_argument(
        "--cash",
        type=float,
        default=2000,
        help="Available capital",
    )
    analyze_parser.add_argument(
        "--risk",
        type=float,
        default=1,
        help="Risk per trade in percent",
    )

    scan_parser = subparsers.add_parser(
        "scan",
        help="Rank stocks from a watchlist",
    )
    scan_parser.add_argument(
        "--tickers",
        default=",".join(DEFAULT_SCAN_TICKERS),
        help="Comma-separated ticker list",
    )

    monitor_parser = subparsers.add_parser("monitor", help="Monitor a watchlist and alert Telegram on material signal changes")
    monitor_parser.add_argument("--tickers", default=",".join(DEFAULT_SCAN_TICKERS), help="Comma-separated ticker list")
    monitor_parser.add_argument("--cash", type=float, default=2000, help="Available capital")
    monitor_parser.add_argument("--risk", type=float, default=1, help="Risk per trade in percent")
    monitor_parser.add_argument("--interval-minutes", type=float, help="Repeat at this interval; omit for one check")
    monitor_parser.add_argument("--no-send", action="store_true", help="Show changed signals but do not contact Telegram")
    monitor_parser.add_argument("--daily-report", action="store_true", help="Send the top five buy and sell rankings, even if nothing changed")
    monitor_parser.add_argument("--universe", action="store_true", help="Scan enabled stocks and ETFs from data/market_universe.csv")
    monitor_parser.add_argument("--portfolio", default="config/portfolio.json", help="Portfolio JSON used for daily holding summaries")
    monitor_parser.add_argument("--rebound-top", type=int, default=5, help="Number of recent-pullback recovery candidates to include")
    scan_parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="Number of results",
    )
    scan_parser.add_argument(
        "--cash",
        type=float,
        default=2000,
        help="Available capital",
    )
    scan_parser.add_argument(
        "--risk",
        type=float,
        default=1,
        help="Risk per trade in percent",
    )

    return parser


def interactive_mode() -> None:
    print("AI Stock Research Assistant")
    print("Examples:")
    print("  Analyze NVDA")
    print("  What should I buy today?")
    print("  What should I sell today?")
    print("  Exit")

    while True:
        question = input("\nAsk: ").strip()

        if not question:
            continue

        if question.lower() in {"exit", "quit", "q"}:
            print("Goodbye.")
            break

        lowered = question.lower()

        try:
            if lowered.startswith("analyze "):
                ticker = question.split(maxsplit=1)[1].strip().upper()
                result = analyze_stock(ticker)
                print_result(result)

            elif "what should i buy" in lowered or "buy today" in lowered:
                result = scan_market(DEFAULT_SCAN_TICKERS, top_n=5)
                print_result(result)

            elif "what should i sell" in lowered or "sell today" in lowered:
                result = scan_sell_candidates(
                    tickers=DEFAULT_SCAN_TICKERS,
                    cash=2000,
                    risk_percent=1,
                    top_n=5,
                )
                print_result(result)

            else:
                print(
                    "Supported questions: "
                    "'Analyze NVDA', "
                    "'What should I buy today?', "
                    "and 'What should I sell today?'"
                )

        except Exception as error:
            print(f"Analysis failed: {error}")


def run_cli() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "analyze":
            result = analyze_stock(
                ticker=args.ticker,
                cash=args.cash,
                risk_percent=args.risk,
            )
            print_result(result)

        elif args.command == "scan":
            tickers = [
                ticker.strip().upper()
                for ticker in args.tickers.split(",")
                if ticker.strip()
            ]

            result = scan_market(
                tickers=tickers,
                cash=args.cash,
                risk_percent=args.risk,
                top_n=args.top,
            )
            print_result(result)

        elif args.command == "monitor":
            portfolio = load_portfolio(args.portfolio)
            selected = load_market_universe() if args.universe else [ticker.strip().upper() for ticker in args.tickers.split(",") if ticker.strip()]
            tickers = list(dict.fromkeys([*selected, *(holding.ticker for holding in portfolio)]))
            options = {"cash": args.cash, "risk_percent": args.risk, "send": not args.no_send, "daily_report": args.daily_report, "portfolio": portfolio, "rebound_top": args.rebound_top}
            if args.interval_minutes:
                run_continuously(tickers, args.interval_minutes, **options)
            else:
                changed = run_monitor_once(tickers, **options)
                if changed:
                    print(f"Monitor completed with {len(changed)} changed signals; report details omitted from logs.")
                else:
                    print("No material signal changes; no Telegram alert sent.")

        else:
            interactive_mode()

    except KeyboardInterrupt:
        print("\nStopped by user.")

    except Exception as error:
        print(f"\nError: {error}")
        raise SystemExit(1) from error
