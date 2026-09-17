from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .data_guard import DataGuard, GuardReport
from .market import YahooMarketData, normalize_ticker
from .ml import HybridPredictor, Prediction


@dataclass
class AnalysisResult:
    ticker: str
    prediction: Prediction
    data: pd.DataFrame
    guard: GuardReport
    market_dataset_count: int


class AnalysisEngine:
    def __init__(self, market: YahooMarketData | None = None):
        self.market = market or YahooMarketData()
        self.guard = DataGuard()
        self.predictor = HybridPredictor()

    def analyze(self, ticker: str, horizon_days: int = 5) -> AnalysisResult:
        ticker = normalize_ticker(ticker)
        data = self.market.history(ticker, period="5y", interval="1d")
        report = self.guard.inspect(data)
        if report.blocked:
            reason = next((x.message for x in report.issues if x.severity == "BLOCK"), "Data Guard blocked")
            raise RuntimeError(reason)

        universe = self.market.history_universe(ticker, period="5y")
        clean_universe: dict[str, pd.DataFrame] = {}
        for symbol, peer in universe.items():
            try:
                peer_report = self.guard.inspect(peer)
                if not peer_report.blocked and len(peer_report.data) >= 180:
                    clean_universe[symbol] = peer_report.data
            except Exception:
                continue

        prediction = self.predictor.predict(report, clean_universe, horizon_days=horizon_days)
        return AnalysisResult(ticker, prediction, report.data, report, len(clean_universe))
