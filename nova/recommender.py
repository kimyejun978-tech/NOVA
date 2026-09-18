from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, brier_score_loss

from .data_guard import DataGuard, GuardReport
from .market import YahooMarketData
from .ml import FEATURES, build_feature_frame


KOREA_SCAN_UNIVERSE = [
    ("005930.KS", "삼성전자"),
    ("000660.KS", "SK하이닉스"),
    ("373220.KS", "LG에너지솔루션"),
    ("207940.KS", "삼성바이오로직스"),
    ("005380.KS", "현대차"),
    ("000270.KS", "기아"),
    ("068270.KS", "셀트리온"),
    ("035420.KS", "NAVER"),
    ("035720.KS", "카카오"),
    ("105560.KS", "KB금융"),
    ("055550.KS", "신한지주"),
    ("051910.KS", "LG화학"),
    ("006400.KS", "삼성SDI"),
    ("066570.KS", "LG전자"),
    ("012330.KS", "현대모비스"),
    ("028260.KS", "삼성물산"),
]

US_SCAN_UNIVERSE = [
    ("AAPL", "Apple"),
    ("MSFT", "Microsoft"),
    ("NVDA", "NVIDIA"),
    ("AMZN", "Amazon"),
    ("META", "Meta"),
    ("GOOGL", "Alphabet"),
    ("TSLA", "Tesla"),
    ("AVGO", "Broadcom"),
    ("AMD", "AMD"),
    ("JPM", "JPMorgan"),
    ("XOM", "Exxon Mobil"),
    ("COST", "Costco"),
    ("NFLX", "Netflix"),
    ("LLY", "Eli Lilly"),
    ("V", "Visa"),
    ("WMT", "Walmart"),
]


@dataclass
class Candidate:
    ticker: str
    name: str
    score: float
    up_probability: float
    confidence: float
    current_price: float
    expected_low_price: float
    expected_high_price: float
    data_quality: float
    data_tier: str
    risk: str
    reason: str
    model_agreement: float


@dataclass
class RecommendationResult:
    market: str
    horizon_days: int
    candidates: list[Candidate]
    scanned: int
    usable: int
    global_accuracy: float
    global_brier: float


def scan_universe(market: str) -> list[tuple[str, str]]:
    return list(KOREA_SCAN_UNIVERSE if market.upper() == "KR" else US_SCAN_UNIVERSE)


def _model(seed: int, trees: int = 260) -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=trees,
        max_depth=7,
        min_samples_leaf=5,
        max_features="sqrt",
        class_weight="balanced_subsample",
        random_state=seed,
        n_jobs=-1,
    )


def _split_frame(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame] | None:
    clean = frame.dropna(subset=FEATURES + ["future_return"]).copy()
    if len(clean) < 160 or clean["target"].nunique() < 2:
        return None
    split = max(120, int(len(clean) * 0.82))
    split = min(split, len(clean) - 25)
    return clean.iloc[:split], clean.iloc[split:]


def _fit_stock(frame: pd.DataFrame, latest: pd.Series, seed: int) -> tuple[float, float, int] | None:
    parts = _split_frame(frame)
    if parts is None:
        return None
    train, test = parts
    model = _model(seed, 180)
    model.fit(train[FEATURES], train["target"].astype(int))
    probs = model.predict_proba(test[FEATURES])[:, 1]
    acc = float(accuracy_score(test["target"].astype(int), probs >= 0.5))

    all_rows = pd.concat([train, test], ignore_index=True)
    model.fit(all_rows[FEATURES], all_rows["target"].astype(int))
    p = float(model.predict_proba(latest.to_frame().T)[0, 1])
    return p, acc, len(all_rows)


def _risk_label(vol20: float) -> str:
    if vol20 < 0.015:
        return "낮음"
    if vol20 < 0.030:
        return "보통"
    return "높음"


def _candidate_reason(latest: pd.Series, agreement: float) -> str:
    parts: list[str] = []
    ret20 = float(latest["ret20"])
    ret5 = float(latest["ret5"])
    volume = float(latest["volume_ratio"])
    if ret20 > 0.05:
        parts.append("20일 모멘텀 강세")
    elif ret20 < -0.05:
        parts.append("20일 모멘텀 약세")
    elif ret5 > 0.02:
        parts.append("단기 모멘텀 개선")
    else:
        parts.append("가격 흐름 중립")

    if volume >= 1.35:
        parts.append("거래량 증가")
    elif volume <= 0.75:
        parts.append("거래량 감소")

    if agreement >= 0.80:
        parts.append("모델 의견 일치")
    elif agreement < 0.50:
        parts.append("모델 의견 엇갈림")
    return " · ".join(parts)


def _ranking_score(up: float, confidence: float, quality: float, agreement: float) -> float:
    # Research-candidate score only. It is intentionally not connected to PaperBroker.
    value = 0.46 * up + 0.30 * confidence + 0.14 * quality + 0.10 * agreement
    return float(max(0.0, min(1.0, value)) * 100.0)


class RecommendationEngine:
    """Paper-research candidate scanner. This class has no broker or rule access."""

    def __init__(self, market: YahooMarketData | None = None):
        self.market = market or YahooMarketData()
        self.guard = DataGuard()

    def scan(
        self,
        market_code: str = "KR",
        horizon_days: int = 5,
        limit: int = 5,
        min_confidence: float = 0.45,
        progress: Callable[[int, int, str], None] | None = None,
    ) -> RecommendationResult:
        universe = scan_universe(market_code)
        reports: dict[str, GuardReport] = {}
        frames: dict[str, pd.DataFrame] = {}
        names = dict(universe)

        total = len(universe)
        for idx, (ticker, _name) in enumerate(universe, 1):
            if progress:
                progress(idx - 1, total, f"{ticker} 데이터 확인")
            try:
                data = self.market.history(ticker, period="5y", interval="1d")
                report = self.guard.inspect(data)
                if report.blocked or len(report.data) < 180:
                    continue
                frame = build_feature_frame(report.data, horizon_days)
                if frame[FEATURES].dropna().empty:
                    continue
                reports[ticker] = report
                frames[ticker] = frame
            except Exception:
                continue

        if progress:
            progress(total, total, "ML 스크리너 학습")

        train_parts: list[pd.DataFrame] = []
        test_parts: list[pd.DataFrame] = []
        for ticker, frame in frames.items():
            parts = _split_frame(frame)
            if parts is None:
                continue
            train, test = parts
            train = train.copy()
            test = test.copy()
            train["__ticker"] = ticker
            test["__ticker"] = ticker
            train_parts.append(train)
            test_parts.append(test)

        if len(train_parts) < 3:
            raise RuntimeError("후보 탐색에 필요한 정상 종목 데이터가 부족합니다.")

        train = pd.concat(train_parts, ignore_index=True)
        test = pd.concat(test_parts, ignore_index=True)
        global_model = _model(1729, 300)
        global_model.fit(train[FEATURES], train["target"].astype(int))
        test_probs = global_model.predict_proba(test[FEATURES])[:, 1]
        global_accuracy = float(accuracy_score(test["target"].astype(int), test_probs >= 0.5))
        global_brier = float(brier_score_loss(test["target"].astype(int), test_probs))

        all_rows = pd.concat([train, test], ignore_index=True)
        global_model.fit(all_rows[FEATURES], all_rows["target"].astype(int))

        preliminary: list[tuple[float, str, pd.Series, float]] = []
        for ticker, frame in frames.items():
            latest_rows = frame[FEATURES].dropna()
            if latest_rows.empty:
                continue
            latest = latest_rows.iloc[-1]
            gp = float(global_model.predict_proba(latest.to_frame().T)[0, 1])
            # A small momentum component is only used to decide which stocks deserve
            # the slower stock-specific second pass.
            momentum = float(np.clip(0.5 + latest["ret20"] * 2.5 + latest["ret5"] * 1.5, 0, 1))
            pre = 0.75 * gp + 0.15 * reports[ticker].quality_score + 0.10 * momentum
            preliminary.append((pre, ticker, latest, gp))

        preliminary.sort(reverse=True, key=lambda x: x[0])
        deep_count = min(len(preliminary), max(8, limit * 2))
        shortlist = preliminary[:deep_count]

        skill = float(np.clip((global_accuracy - 0.50) / 0.20, 0, 1))
        candidates: list[Candidate] = []
        for deep_idx, (_pre, ticker, latest, global_p) in enumerate(shortlist, 1):
            if progress:
                progress(total, total, f"{ticker} 정밀 분석 {deep_idx}/{deep_count}")

            report = reports[ticker]
            stock_result = None
            if report.usable_for_stock_model:
                try:
                    stock_result = _fit_stock(frames[ticker], latest, seed=100 + deep_idx)
                except Exception:
                    stock_result = None

            if stock_result:
                stock_p, stock_acc, stock_samples = stock_result
                stock_weight = {"FULL": 0.58, "STANDARD": 0.48, "LIMITED": 0.32}.get(report.tier, 0.0)
                up = stock_p * stock_weight + global_p * (1.0 - stock_weight)
                agreement = 1.0 - min(1.0, abs(stock_p - global_p) / 0.50)
                local_skill = float(np.clip((stock_acc - 0.50) / 0.20, 0, 1))
                model_skill = 0.65 * skill + 0.35 * local_skill
                sample_score = min(1.0, stock_samples / 1000.0)
            else:
                up = global_p
                agreement = 0.58
                model_skill = skill
                sample_score = min(1.0, len(frames[ticker]) / 1000.0)

            confidence = float(np.clip(
                0.34 * report.quality_score
                + 0.30 * model_skill
                + 0.22 * agreement
                + 0.14 * sample_score,
                0,
                1,
            ))

            trainable = frames[ticker]["future_return"].dropna().tail(300)
            if len(trainable) < 40:
                continue
            low_pct = float(trainable.quantile(0.10))
            high_pct = float(trainable.quantile(0.90))
            current = float(report.data["Close"].dropna().iloc[-1])
            score = _ranking_score(up, confidence, report.quality_score, agreement)

            # Do not force a recommendation. Weak/uncertain results are omitted.
            if confidence < min_confidence or up < 0.52 or report.quality_score < 0.65:
                continue

            candidates.append(Candidate(
                ticker=ticker,
                name=names.get(ticker, ticker),
                score=score,
                up_probability=float(up),
                confidence=confidence,
                current_price=current,
                expected_low_price=current * (1.0 + low_pct),
                expected_high_price=current * (1.0 + high_pct),
                data_quality=report.quality_score,
                data_tier=report.tier,
                risk=_risk_label(float(latest["vol20"])),
                reason=_candidate_reason(latest, agreement),
                model_agreement=agreement,
            ))

        candidates.sort(key=lambda x: (x.score, x.confidence), reverse=True)
        return RecommendationResult(
            market=market_code.upper(),
            horizon_days=horizon_days,
            candidates=candidates[: max(1, limit)],
            scanned=total,
            usable=len(frames),
            global_accuracy=global_accuracy,
            global_brier=global_brier,
        )
