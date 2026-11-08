from agents.news import analyze_news
from providers.google_news import NewsItem


def test_analyze_news_scores_headline_signal(monkeypatch):
    monkeypatch.setattr(
        "agents.news.fetch_news",
        lambda ticker: (
            [
                NewsItem("Company beats estimates after strong growth", "", "Source", "", ""),
                NewsItem("Analyst upgrade follows record profit", "", "Source", "", ""),
            ],
            "https://example.com",
        ),
    )

    result = analyze_news("NVDA")

    assert result.score > 50
    assert result.sentiment == "Positive"
    assert result.article_count == 2


def test_analyze_news_marks_missing_headlines_as_unavailable(monkeypatch):
    monkeypatch.setattr("agents.news.fetch_news", lambda ticker: ([], "https://example.com"))

    result = analyze_news("NVDA")

    assert result.score == 50
    assert result.sentiment == "Unavailable"
