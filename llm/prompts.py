def news_prompt(ticker: str, headlines: str) -> str:
    return f"""
You are an equity news analyst. Analyze recent headlines for {ticker}.
Return exactly:
Sentiment: Bullish/Neutral/Bearish
Score: 0-100
Summary: 3 concise bullet points
Risks: 2 concise bullet points

Headlines:
{headlines}
""".strip()
