from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")
    default_watchlist: str = os.getenv(
        "DEFAULT_WATCHLIST",
        "NVDA,AVGO,MSFT,AAPL,GOOGL,AMZN,META,ASML,TSM,RHM.DE,SPY,QQQ",
    )
    reports_dir: str = "reports"
    data_dir: str = "data"


settings = Settings()
