from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class SourceLink:
    name: str
    url: str


@dataclass
class TechnicalResult:
    ticker: str
    price: float
    score: float
    trend: str
    momentum: str
    rsi: float
    macd: float
    macd_signal: float
    sma20: float
    sma50: float
    atr: float
    adx: float
    support: float
    resistance: float
    notes: list[str] = field(default_factory=list)
    sources: list[SourceLink] = field(default_factory=list)


@dataclass
class FundamentalResult:
    ticker: str
    score: float
    metrics: dict
    notes: list[str] = field(default_factory=list)
    sources: list[SourceLink] = field(default_factory=list)


@dataclass
class NewsResult:
    ticker: str
    score: float
    sentiment: str
    notes: list[str] = field(default_factory=list)
    sources: list[SourceLink] = field(default_factory=list)


@dataclass
class RiskResult:
    ticker: str
    score: float
    stop_loss: float
    take_profit: float
    position_size: float
    shares: int
    risk_amount: float
    notes: list[str] = field(default_factory=list)
    sources: list[SourceLink] = field(default_factory=list)


@dataclass
class DecisionResult:
    ticker: str
    final_score: float
    decision: str
    confidence: str
    reasons: list[str]
    sources: list[SourceLink]
    components: dict[str, float]


@dataclass
class StockAnalysisResult:
    ticker: str

    # Scores
    technical_score: float
    fundamental_score: float
    news_score: float
    risk_score: float
    final_score: float

    # Decision
    recommendation: str
    confidence: float = 0.0

    # Technical
    trend: str = "Unknown"

    # News
    news_sentiment: str = "Neutral"
    news_article_count: int = 0
    news_headlines: List[str] = field(default_factory=list)

    # Fundamentals
    pe_ratio: float | None = None
    revenue_growth: float | None = None
    eps_growth: float | None = None

    # Risk
    volatility: float | None = None
    beta: float | None = None

    # AI
    summary: str = ""
