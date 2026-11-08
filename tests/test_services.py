from types import SimpleNamespace

from app.services import StockAnalysisResult, analyze_stock, scan_market


def test_analyze_stock_returns_result(monkeypatch):
    monkeypatch.setattr(
        "app.services.get_market_data",
        lambda ticker: SimpleNamespace(history=object(), references={"Yahoo": "example.com"}),
    )
    monkeypatch.setattr(
        "app.services.analyze_technical",
        lambda ticker, history: SimpleNamespace(
            price=100.0,
            score=80.0,
            trend="Bullish",
            momentum="Positive",
            rsi=55.0,
            macd=1.0,
            macd_signal=0.5,
            sma20=98.0,
            sma50=95.0,
            atr=2.0,
            adx=30.0,
            support=90.0,
            resistance=110.0,
            notes=["Positive trend"],
        ),
    )
    monkeypatch.setattr(
        "app.services.analyze_news",
        lambda ticker: SimpleNamespace(
            score=70.0,
            sentiment="Positive",
            summary="Positive headlines.",
            article_count=3,
        ),
    )
    monkeypatch.setattr(
        "app.services.analyze_fundamentals",
        lambda ticker: SimpleNamespace(score=50.0, notes=["Neutral fundamentals"], sources=[]),
    )
    monkeypatch.setattr(
        "app.services.analyze_risk",
        lambda ticker, technical, cash, risk_percent: SimpleNamespace(score=50.0, notes=["Neutral risk"], sources=[]),
    )

    result = analyze_stock("NVDA")

    assert result.ticker == "NVDA"
    assert result.final_score == 65.0
    assert result.decision == "Strong buy setup"
    assert result.news_score == 70.0
    assert result.news_sentiment == "Positive"


def test_scan_market_returns_top_results(monkeypatch):
    scores = {"NVDA": 55.0, "AVGO": 62.0, "MSFT": 58.0}

    def fake_analyze_stock(ticker, cash, risk_percent):
        return StockAnalysisResult(
            ticker=ticker,
            price=100.0,
            technical_score=scores[ticker],
            fundamental_score=50.0,
            news_score=50.0,
            risk_score=50.0,
            final_score=scores[ticker],
            decision="Watch",
            notes=[],
            references={},
        )

    monkeypatch.setattr("app.services.analyze_stock", fake_analyze_stock)

    results = scan_market(["NVDA", "AVGO", "MSFT"], top_n=2)

    assert [result.ticker for result in results] == ["AVGO", "MSFT"]


def test_scan_market_ranks_dataclass_results_and_passes_scan_settings(monkeypatch):
    seen_calls = []

    def fake_analyze_stock(ticker, cash, risk_percent):
        seen_calls.append((ticker, cash, risk_percent))
        return StockAnalysisResult(
            ticker=ticker,
            price=100.0,
            technical_score={"AAA": 75.0, "BBB": 80.0, "CCC": 80.0}[ticker],
            fundamental_score=50.0,
            news_score=50.0,
            risk_score=50.0,
            final_score={"AAA": 60.0, "BBB": 62.0, "CCC": 62.0}[ticker],
            decision="Watch",
            notes=[],
            references={},
        )

    monkeypatch.setattr("app.services.analyze_stock", fake_analyze_stock)

    results = scan_market(
        ["aaa", "BBB", "AAA", "CCC"], cash=5000, risk_percent=2, top_n=2
    )

    assert [result.ticker for result in results] == ["BBB", "CCC"]
    assert seen_calls == [("AAA", 5000, 2), ("BBB", 5000, 2), ("CCC", 5000, 2)]


def test_scan_market_loads_default_csv_universe(monkeypatch):
    seen_arguments = {}

    def fake_load_market_universe(asset_types, limit):
        seen_arguments.update(asset_types=asset_types, limit=limit)
        return ["NVDA"]

    monkeypatch.setattr("app.services.load_market_universe", fake_load_market_universe)
    monkeypatch.setattr(
        "app.services.analyze_stock",
        lambda ticker, cash, risk_percent: StockAnalysisResult(
            ticker=ticker,
            price=100.0,
            technical_score=70.0,
            fundamental_score=50.0,
            news_score=50.0,
            risk_score=50.0,
            final_score=57.0,
            decision="Possible buy",
            notes=[],
            references={},
        ),
    )

    results = scan_market(asset_types=["ETF"], universe_limit=500)

    assert [result.ticker for result in results] == ["NVDA"]
    assert seen_arguments == {"asset_types": ["ETF"], "limit": 500}
