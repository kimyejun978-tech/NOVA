from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import time

import pandas as pd
import yfinance as yf

from .config import (
    CACHE_DIR,
    COMMON_TICKERS,
    HISTORY_CACHE_HOURS,
    KOREA_BASE_UNIVERSE,
    US_BASE_UNIVERSE,
)


@dataclass
class Quote:
    ticker: str
    price: float
    timestamp: str
    source: str = "Yahoo Finance"


def normalize_ticker(raw: str) -> str:
    text = raw.strip()
    if not text:
        raise ValueError("종목 코드를 입력하세요.")

    mapped = COMMON_TICKERS.get(text)
    if mapped:
        return mapped

    upper = text.upper()
    mapped = COMMON_TICKERS.get(upper)
    if mapped:
        return mapped

    if upper.isdigit() and len(upper) == 6:
        return f"{upper}.KS"
    return upper


def base_universe(ticker: str) -> list[str]:
    ticker = normalize_ticker(ticker)
    if ticker.endswith((".KS", ".KQ")):
        items = list(KOREA_BASE_UNIVERSE)
    else:
        items = list(US_BASE_UNIVERSE)
    if ticker not in items:
        items.insert(0, ticker)
    return items


class YahooMarketData:
    def _cache_path(self, ticker: str, period: str, interval: str) -> Path:
        safe = ticker.replace("^", "IDX_").replace("/", "_")
        return CACHE_DIR / f"{safe}_{period}_{interval}.pkl"

    def history(self, ticker: str, period: str = "5y", interval: str = "1d", force: bool = False) -> pd.DataFrame:
        ticker = normalize_ticker(ticker)
        cache = self._cache_path(ticker, period, interval)
        max_age = HISTORY_CACHE_HOURS * 3600
        if not force and cache.exists() and time.time() - cache.stat().st_mtime < max_age:
            try:
                cached = pd.read_pickle(cache)
                if cached is not None and not cached.empty:
                    return cached.copy()
            except Exception:
                pass

        data = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=True, actions=True)
        if data is None or data.empty:
            raise RuntimeError(f"{ticker}의 가격 데이터를 가져오지 못했습니다.")
        data = data.copy()
        data.columns = [str(c).title() for c in data.columns]
        data = data.dropna(subset=["Close"])
        try:
            data.to_pickle(cache)
        except Exception:
            pass
        return data

    def history_universe(self, ticker: str, period: str = "5y") -> dict[str, pd.DataFrame]:
        result: dict[str, pd.DataFrame] = {}
        for symbol in base_universe(ticker):
            try:
                result[symbol] = self.history(symbol, period=period, interval="1d")
            except Exception:
                continue
        return result

    def quote(self, ticker: str) -> Quote:
        ticker = normalize_ticker(ticker)
        obj = yf.Ticker(ticker)
        intraday = obj.history(period="5d", interval="1m", auto_adjust=False)
        if intraday is None or intraday.empty:
            intraday = obj.history(period="1mo", interval="1d", auto_adjust=False)
        if intraday is None or intraday.empty:
            raise RuntimeError(f"{ticker}의 현재가를 가져오지 못했습니다.")
        clean = intraday.dropna(subset=["Close"])
        row = clean.iloc[-1]
        ts = str(clean.index[-1])
        return Quote(ticker=ticker, price=float(row["Close"]), timestamp=ts)
