from __future__ import annotations

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from app.models import TechnicalResult, FundamentalResult, NewsResult, RiskResult, DecisionResult


def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(Path(__file__).parent / "templates")),
        autoescape=select_autoescape(["html", "xml"]),
    )


def create_stock_report(
    ticker: str,
    technical: TechnicalResult,
    fundamentals: FundamentalResult,
    news: NewsResult,
    risk: RiskResult,
    decision: DecisionResult,
    chart_path: str,
    output_dir: str = "reports",
) -> str:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    template = _env().get_template("stock_report.html")
    html = template.render(
        ticker=ticker,
        technical=technical,
        fundamentals=fundamentals,
        news=news,
        risk=risk,
        decision=decision,
        chart_path=Path(chart_path).name,
    )
    path = Path(output_dir) / f"{ticker}_report.html"
    path.write_text(html, encoding="utf-8")
    return str(path.resolve())


def create_scan_report(candidates, output_dir: str = "reports") -> str:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    template = _env().get_template("scan_report.html")
    html = template.render(candidates=candidates)
    path = Path(output_dir) / "today_scan_report.html"
    path.write_text(html, encoding="utf-8")
    return str(path.resolve())
