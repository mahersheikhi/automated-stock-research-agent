"""Minimal Telegram Bot API provider used by the market monitor."""
from __future__ import annotations

import requests


TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


def send_telegram_message(token: str, chat_id: str, text: str) -> None:
    """Send a Markdown-free message through Telegram's Bot API.

    Credentials are supplied by configuration; they are never logged or stored.
    """
    if not token or not chat_id:
        raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env")

    try:
        response = requests.post(
        TELEGRAM_API_URL.format(token=token),
        json={"chat_id": chat_id, "text": text, "disable_web_page_preview": True},
        timeout=15,
    )
        response.raise_for_status()
    except requests.RequestException:
        raise RuntimeError("Telegram delivery failed; check credentials and connectivity.") from None
