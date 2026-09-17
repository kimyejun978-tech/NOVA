from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, brier_score_loss

from .data_guard import GuardReport


FEATURES = [
    "ret1", "ret5", "ret20", "sma5_rel", "sma20_rel", "sma60_rel",
    "ema12_rel", "ema26_rel", "rsi14", "vol20", "vol60",
    "volume_ratio", "range_pct", "macd_rel",
]


@dataclass
class ModelResult:
    probability: float
    accuracy: float
    brier: float
    samples: int


@dataclass
class Prediction:
    horizon_days: int
    up_probability: float
    down_probability: float
    model_score: float
    test_accuracy: float
    brier_score: float
    expected_low_pct: float
    expected_high_pct: float
    current_price: float
    expected_low_price: float
    expected_high_price: float
    feature_values: Dict[str, float]
    samples: int
    stock_probability: float | None
    global_probability: float | None
    stock_accuracy: float | None
    global_accuracy: float | None
    stock_samples: int
    global_samples: int
    data_quality: float
    data_tier: str
    model_agreement: float
    confidence_reasons: list[str]


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    avg_gain = up.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = down.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def build_feature_frame(data: pd.DataFrame, horizon_days: int) -> pd.DataFrame:
    df = data.copy()
    close = df["Close"].astype(float)
    high = df["High"].astype(float)
    low = df["Low"].astype(float)
    volume = df["Volume"].astype(float).replace(0, np.nan)

    df["ret1"] = close.pct_change(1)
    df["ret5"] = close.pct_change(5)
    df["ret20"] = close.pct_change(20)
    df["sma5_rel"] = close / close.rolling(5).mean() - 1
    df["sma20_rel"] = close / close.rolling(20).mean() - 1
    df["sma60_rel"] = close / close.rolling(60).mean() - 1
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df["ema12_rel"] = close / ema12 - 1
    df["ema26_rel"] = close / ema26 - 1
    df["rsi14"] = _rsi(close) / 100.0
    daily = close.pct_change()
    df["vol20"] = daily.rolling(20).std()
    df["vol60"] = daily.rolling(60).std()
    df["volume_ratio"] = volume / volume.rolling(20).mean()
    df["range_pct"] = (high - low) / close.replace(0, np.nan)
    df["macd_rel"] = (ema12 - ema26) / close.replace(0, np.nan)

    df["future_return"] = close.shift(-horizon_days) / close - 1
    df["target"] = (df["future_return"] > 0).astype(int)
    return df


def _make_model(seed: int = 42) -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=360,
        max_depth=7,
        min_samples_leaf=5,
        max_features="sqrt",
        class_weight="balanced_subsample",
        random_state=seed,
        n_jobs=-1,
    )


def _fit_one(trainable: pd.DataFrame, latest: pd.Series, seed: int = 42) -> ModelResult:
    X = trainable[FEATURES]
    y = trainable["target"].astype(int)
    if len(trainable) < 100 or y.nunique() < 2:
        raise RuntimeError("상승/하락 학습 표본이 충분하지 않습니다.")

    split = max(80, int(len(trainable) * 0.8))
    split = min(split, len(trainable) - 20)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    model = _make_model(seed)
    model.fit(X_train, y_train)
    probs = model.predict_proba(X_test)[:, 1]
    preds = (probs >= 0.5).astype(int)
    acc = float(accuracy_score(y_test, preds))
    brier = float(brier_score_loss(y_test, probs))

    model.fit(X, y)
    p = float(model.predict_proba(latest.to_frame().T)[0, 1])
    return ModelResult(p, acc, brier, len(trainable))


def _global_train_test(frames: Iterable[pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    train_parts: list[pd.DataFrame] = []
    test_parts: list[pd.DataFrame] = []
    for frame in frames:
        t = frame.dropna(subset=FEATURES + ["future_return"]).copy()
        if len(t) < 120 or t["target"].nunique() < 2:
            continue
        split = max(90, int(len(t) * 0.8))
        split = min(split, len(t) - 20)
        train_parts.append(t.iloc[:split])
        test_parts.append(t.iloc[split:])
    if not train_parts or not test_parts:
        raise RuntimeError("Global Model을 만들 수 있는 시장 데이터가 부족합니다.")
    return pd.concat(train_parts, ignore_index=True), pd.concat(test_parts, ignore_index=True)


def _fit_global(datasets: Iterable[pd.DataFrame], horizon: int, latest: pd.Series) -> ModelResult:
    frames = [build_feature_frame(df, horizon) for df in datasets]
    train, test = _global_train_test(frames)
    X_train, y_train = train[FEATURES], train["target"].astype(int)
    X_test, y_test = test[FEATURES], test["target"].astype(int)

    model = _make_model(84)
    model.fit(X_train, y_train)
    probs = model.predict_proba(X_test)[:, 1]
    preds = (probs >= 0.5).astype(int)
    acc = float(accuracy_score(y_test, preds))
    brier = float(brier_score_loss(y_test, probs))

    all_rows = pd.concat([train, test], ignore_index=True)
    model.fit(all_rows[FEATURES], all_rows["target"].astype(int))
    p = float(model.predict_proba(latest.to_frame().T)[0, 1])
    return ModelResult(p, acc, brier, len(all_rows))


class HybridPredictor:
    """Global market model + selected-stock model with confidence estimation."""

    def predict(
        self,
        guard: GuardReport,
        market_datasets: dict[str, pd.DataFrame],
        horizon_days: int = 5,
    ) -> Prediction:
        if guard.blocked:
            reason = next((x.message for x in guard.issues if x.severity == "BLOCK"), "Data Guard 차단")
            raise RuntimeError(reason)

        data = guard.data
        frame = build_feature_frame(data, horizon_days)
        latest_rows = frame[FEATURES].dropna()
        if latest_rows.empty:
            raise RuntimeError("최신 시점의 ML feature를 계산할 수 없습니다.")
        latest = latest_rows.iloc[-1]
        trainable = frame.dropna(subset=FEATURES + ["future_return"]).copy()

        stock: ModelResult | None = None
        if guard.usable_for_stock_model and len(trainable) >= 180:
            stock = _fit_one(trainable, latest, 42)

        usable_global = [d for d in market_datasets.values() if d is not None and len(d) >= 180]
        global_result: ModelResult | None = None
        if len(usable_global) >= 2:
            try:
                global_result = _fit_global(usable_global, horizon_days, latest)
            except Exception:
                global_result = None

        if stock is None and global_result is None:
            raise RuntimeError("종목 전용 모델과 Global Model 모두 학습 가능한 데이터가 부족합니다.")

        if stock and global_result:
            stock_weight = {"FULL": 0.62, "STANDARD": 0.52, "LIMITED": 0.36}.get(guard.tier, 0.0)
            global_weight = 1.0 - stock_weight
            up = stock.probability * stock_weight + global_result.probability * global_weight
            agreement = 1.0 - min(1.0, abs(stock.probability - global_result.probability) / 0.50)
        elif stock:
            up = stock.probability
            agreement = 0.62
        else:
            up = global_result.probability
            agreement = 0.58

        weighted_acc_parts = []
        weighted_brier_parts = []
        if stock:
            weighted_acc_parts.append(stock.accuracy)
            weighted_brier_parts.append(stock.brier)
        if global_result:
            weighted_acc_parts.append(global_result.accuracy)
            weighted_brier_parts.append(global_result.brier)
        acc = float(np.mean(weighted_acc_parts))
        brier = float(np.mean(weighted_brier_parts))

        skill = max(0.0, min(1.0, (acc - 0.50) / 0.20))
        sample_base = (stock.samples if stock else 0) + min(2500, global_result.samples if global_result else 0)
        sample_score = min(1.0, sample_base / 2500.0)
        confidence = (
            0.33 * guard.quality_score
            + 0.31 * skill
            + 0.21 * agreement
            + 0.15 * sample_score
        )
        confidence = float(max(0.0, min(1.0, confidence)))

        recent_returns = trainable["future_return"].tail(300)
        if len(recent_returns) < 40:
            recent_returns = frame["future_return"].dropna()
        low_pct = float(recent_returns.quantile(0.10))
        high_pct = float(recent_returns.quantile(0.90))
        current = float(data["Close"].dropna().iloc[-1])

        reasons = [
            f"Data quality {guard.quality_score * 100:.0f}/100 ({guard.tier})",
            f"Model agreement {agreement * 100:.0f}/100",
            f"Held-out accuracy {acc * 100:.1f}%",
        ]
        if stock is None:
            reasons.append("Stock-specific model disabled: insufficient history")
        if global_result is None:
            reasons.append("Global model unavailable: market dataset insufficient")

        return Prediction(
            horizon_days=horizon_days,
            up_probability=float(up),
            down_probability=float(1.0 - up),
            model_score=confidence,
            test_accuracy=acc,
            brier_score=brier,
            expected_low_pct=low_pct,
            expected_high_pct=high_pct,
            current_price=current,
            expected_low_price=current * (1.0 + low_pct),
            expected_high_price=current * (1.0 + high_pct),
            feature_values={k: float(latest[k]) for k in FEATURES},
            samples=(stock.samples if stock else 0) + (global_result.samples if global_result else 0),
            stock_probability=stock.probability if stock else None,
            global_probability=global_result.probability if global_result else None,
            stock_accuracy=stock.accuracy if stock else None,
            global_accuracy=global_result.accuracy if global_result else None,
            stock_samples=stock.samples if stock else 0,
            global_samples=global_result.samples if global_result else 0,
            data_quality=guard.quality_score,
            data_tier=guard.tier,
            model_agreement=agreement,
            confidence_reasons=reasons,
        )

MLPredictor = HybridPredictor
