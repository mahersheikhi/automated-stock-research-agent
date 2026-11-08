
if __name__ == "__main__":
    main()


def scan_today(tickers, cash=2000, risk_percent=1, top_n=5):
    results = []

    for ticker in tickers:
        try:
            technical = run_technical_analysis(ticker)
            fundamentals = run_fundamental_analysis(ticker)
            news = run_news_analysis(ticker)
            risk = run_risk_management(
                ticker=ticker,
                price=technical.price,
                cash=cash,
                risk_percent=risk_percent,
            )
            decision = run_cio_decision(
                ticker=ticker,
                technical=technical,
                fundamentals=fundamentals,
                news=news,
                risk=risk,
            )

            results.append({
                "ticker": ticker,
                "price": round(float(technical.price), 2),
                "technical_score": technical.score,
                "fundamental_score": fundamentals.score,
                "news_score": news.score,
                "risk_score": risk.score,
                "final_score": decision.final_score,
                "decision": decision.decision,
            })

        except Exception as e:
            results.append({
                "ticker": ticker,
                "price": "N/A",
                "final_score": 0,
                "decision": f"Error: {e}",
            })

    results = sorted(results, key=lambda x: x["final_score"], reverse=True)
    return results[:top_n]