from __future__ import annotations

import logging
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "assistant.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("ai-stock-assistant")