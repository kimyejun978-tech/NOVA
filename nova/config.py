from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "NOVA"
APP_VERSION = "1.1.4"

DATA_DIR = Path(os.getenv("LOCALAPPDATA", Path.home())) / APP_NAME
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "nova.db"
CACHE_DIR = DATA_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR = DATA_DIR / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
UPDATE_DIR = DATA_DIR / "update"
UPDATE_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_CASH = 10_000_000.0
DEFAULT_MAX_ORDER_VALUE = 2_000_000.0
DEFAULT_MAX_POSITION_PCT = 25.0
DEFAULT_COOLDOWN_SECONDS = 60
AUTO_SCAN_SECONDS = 60
HISTORY_CACHE_HOURS = 6

UPDATE_OWNER = os.getenv("NOVA_UPDATE_OWNER", "kimyejun978-tech")
UPDATE_REPO = os.getenv("NOVA_UPDATE_REPO", "NOVA")
UPDATE_ASSET_EXE = os.getenv("NOVA_UPDATE_ASSET_EXE", "NOVA-Windows.zip")
UPDATE_ASSET_SOURCE = os.getenv("NOVA_UPDATE_ASSET_SOURCE", "NOVA-Source.zip")

COMMON_TICKERS = {
    "삼성전자": "005930.KS",
    "삼성": "005930.KS",
    "SK하이닉스": "000660.KS",
    "하이닉스": "000660.KS",
    "NAVER": "035420.KS",
    "네이버": "035420.KS",
    "카카오": "035720.KS",
    "현대차": "005380.KS",
    "기아": "000270.KS",
    "AAPL": "AAPL",
    "MSFT": "MSFT",
    "NVDA": "NVDA",
    "TSLA": "TSLA",
}

KOREA_BASE_UNIVERSE = [
    "005930.KS", "000660.KS", "035420.KS", "005380.KS",
    "000270.KS", "051910.KS", "006400.KS", "068270.KS",
]
US_BASE_UNIVERSE = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "JPM", "XOM",
]
