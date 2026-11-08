import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from app.services import analyze_stock, scan_market

st.set_page_config(
    page_title="AI Stock Research Assistant",
    page_icon="📈",
    layout="wide",
)

st.title("📈 AI Stock Research Assistant")

st.sidebar.header("Settings")

ticker = st.sidebar.text_input("Ticker", value="NVDA")
cash = st.sidebar.number_input("Cash available", value=2000, step=100)
risk = st.sidebar.number_input("Risk per trade (%)", value=1.0, step=0.5)
asset_types = st.sidebar.multiselect(
    "Universe asset types", options=["STOCK", "ETF"], default=["STOCK", "ETF"]
)
universe_limit = st.sidebar.number_input(
    "Universe scan limit (0 = all enabled symbols)",
    min_value=0,
    max_value=10000,
    value=250,
    step=50,
)


if st.button("🔎 Find Top Opportunities"):

    with st.spinner("Scanning market..."):
        opportunities = scan_market(
            cash=float(cash),
            risk_percent=float(risk),
            asset_types=asset_types,
            universe_limit=None if universe_limit == 0 else int(universe_limit),
        )

    st.subheader("🔥 Top ranked opportunities")

    if not opportunities:
        st.warning("No valid results were returned.")

    eligible = [stock for stock in opportunities if stock.is_eligible]
    waiting = [stock for stock in opportunities if not stock.is_eligible]

    if eligible:
        st.success(f"{len(eligible)} eligible setup(s) met the current entry criteria.")
    else:
        st.info("No eligible setups today. The ranked results below need more confirmation.")

    for rank, stock in enumerate(eligible, start=1):
        st.markdown(
            f"""
            ### Eligible #{rank}: {stock.ticker} — {stock.decision}

            **Opportunity score:** {stock.final_score:.1f}/100<br>
            **Price:** {stock.price:.2f}<br>
            **Technical:** {stock.technical_score:.1f}/100<br>
            **News:** {stock.news_score:.1f}/100 ({stock.news_sentiment}; {stock.news_article_count} headlines)
            """
        )

    if waiting:
        st.caption("Ranked candidates below are not eligible entries yet; they are shown for research and monitoring.")
    for rank, stock in enumerate(waiting, start=len(eligible) + 1):
        st.markdown(
            f"""
            ### Monitor #{rank}: {stock.ticker} — {stock.decision}

            **Opportunity score:** {stock.final_score:.1f}/100<br>
            **Technical:** {stock.technical_score:.1f}/100<br>
            **News:** {stock.news_score:.1f}/100 ({stock.news_sentiment}; {stock.news_article_count} headlines)
            """
        )

if st.sidebar.button("Analyze"):
    with st.spinner(f"Analyzing {ticker}..."):
        result = analyze_stock(ticker=ticker, cash=cash, risk_percent=risk)

    st.success("Analysis complete")

    report_path = ROOT / "reports" / f"{ticker.upper()}_report.html"
    chart_path = ROOT / "reports" / f"{ticker.upper()}_chart.png"

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Report")

        if report_path.exists():

            html_content = report_path.read_text(encoding="utf-8")

            st.components.v1.html(
                html_content,
                height=600,
                scrolling=True
            )

            st.download_button(
                label="📥 Download HTML Report",
                data=html_content,
                file_name=f"{ticker.upper()}_report.html",
                mime="text/html"
            )

    with col2:
        st.subheader("Chart")
        if chart_path.exists():
            st.image(str(chart_path))
        else:
            st.warning("Chart not found.")


st.divider()
st.header("💬 Ask the AI Stock Assistant")

question = st.text_input(
    "Ask a question",
    value="What should I buy today?"
)

watchlist = st.text_input(
    "Watchlist",
    value="NVDA,AVGO,MSFT,ASML,TSM,RHM.DE,SPY"
)

top_n = st.number_input("Top results", value=5, min_value=1, max_value=20)

if st.button("Ask"):
    tickers = [
        item.strip().upper()
        for item in watchlist.split(",")
        if item.strip()
    ]

    with st.spinner("Scanning watchlist..."):
        results = scan_market(
            tickers=tickers,
            cash=float(cash),
            risk_percent=float(risk),
            top_n=int(top_n),
        )

    st.subheader("Today's ranked candidates")

    if not results:
        st.warning("No valid results were returned.")

    eligible = [item for item in results if item.is_eligible]
    waiting = [item for item in results if not item.is_eligible]

    if eligible:
        st.success(f"{len(eligible)} eligible setup(s) found.")
    elif results:
        st.info("No eligible setups found. The candidates below require confirmation.")

    for item in eligible:
        st.markdown(
            f"""
            ### Eligible: {item.ticker}

            **Score:** {item.final_score:.1f}/100<br>
            **Decision:** {item.decision}<br>
            **Price:** {item.price:.2f}<br>
            **Technical:** {item.technical_score:.1f}/100<br>
            **News:** {item.news_score:.1f}/100 ({item.news_sentiment}; {item.news_article_count} headlines)
            """
        )

    for item in waiting:
        st.markdown(
            f"""
            ### Monitor: {item.ticker}

            **Score:** {item.final_score:.1f}/100  
            **Decision:** {item.decision}  
            **Price:** {item.price:.2f}  
            **Technical:** {item.technical_score:.1f}/100  
            **News:** {item.news_score:.1f}/100 ({item.news_sentiment}; {item.news_article_count} headlines)
            """
        )
