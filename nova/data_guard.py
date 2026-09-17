from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import numpy as np
import pandas as pd


@dataclass
class GuardIssue:
    severity: str
    message: str


@dataclass
class GuardReport:
    data: pd.DataFrame
    quality_score: float
    tier: str
    usable_for_stock_model: bool
    issues: List[GuardIssue] = field(default_factory=list)

    @property
    def blocked(self) -> bool:
        return any(x.severity == "BLOCK" for x in self.issues)


class DataGuard:
    """Validates market history before any model can train on it."""

    def inspect(self, data: pd.DataFrame) -> GuardReport:
        if data is None or data.empty:
            raise RuntimeError("가격 데이터가 비어 있습니다.")

        df = data.copy().sort_index()
        issues: list[GuardIssue] = []
        quality = 1.0

        if df.index.has_duplicates:
            duplicated = int(df.index.duplicated(keep="last").sum())
            df = df[~df.index.duplicated(keep="last")]
            issues.append(GuardIssue("WARN", f"중복 시점 {duplicated}건 제거"))
            quality -= 0.05

        required = ["Open", "High", "Low", "Close", "Volume"]
        missing_cols = [c for c in required if c not in df.columns]
        if missing_cols:
            issues.append(GuardIssue("BLOCK", f"필수 가격 열 누락: {', '.join(missing_cols)}"))
            return GuardReport(df, 0.0, "BLOCKED", False, issues)

        for col in ["Open", "High", "Low", "Close"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce")

        invalid_price = (~np.isfinite(df["Close"])) | (df["Close"] <= 0)
        if invalid_price.any():
            count = int(invalid_price.sum())
            issues.append(GuardIssue("WARN", f"비정상 종가 {count}건 제거"))
            df = df.loc[~invalid_price].copy()
            quality -= min(0.25, count / max(1, len(data)))

        bad_ohlc = (
            (df["High"] < df[["Open", "Close", "Low"]].max(axis=1))
            | (df["Low"] > df[["Open", "Close", "High"]].min(axis=1))
        )
        if bad_ohlc.any():
            count = int(bad_ohlc.sum())
            issues.append(GuardIssue("WARN", f"OHLC 관계 이상 {count}건 제외"))
            df = df.loc[~bad_ohlc].copy()
            quality -= min(0.20, count / max(1, len(data)))

        neg_volume = df["Volume"] < 0
        if neg_volume.any():
            count = int(neg_volume.sum())
            issues.append(GuardIssue("WARN", f"음수 거래량 {count}건 제외"))
            df = df.loc[~neg_volume].copy()
            quality -= 0.08

        returns = df["Close"].pct_change()
        extreme = returns.abs() > 0.45
        absurd = returns.abs() > 0.90
        if absurd.any():
            issues.append(GuardIssue("BLOCK", "90%를 넘는 비정상 일간 가격 변화가 발견되어 학습을 중지했습니다."))
            quality = 0.0
        elif extreme.any():
            issues.append(GuardIssue("WARN", f"45% 초과 급변 {int(extreme.sum())}건 감지 — 결과 신뢰도를 낮춥니다."))
            quality -= min(0.18, 0.04 * int(extreme.sum()))

        n = len(df)
        if n >= 1000:
            tier = "FULL"
            usable = True
        elif n >= 500:
            tier = "STANDARD"
            usable = True
        elif n >= 250:
            tier = "LIMITED"
            usable = True
            quality -= 0.08
            issues.append(GuardIssue("INFO", "종목 데이터가 제한적이어서 Global Model 비중을 높입니다."))
        else:
            tier = "GLOBAL_ONLY"
            usable = False
            quality -= 0.20
            issues.append(GuardIssue("WARN", "250거래일 미만이라 종목 전용 ML은 사용하지 않습니다."))

        if n < 120:
            issues.append(GuardIssue("BLOCK", "분석 가능한 최소 과거 데이터(120거래일)가 부족합니다."))
            quality = 0.0

        quality = float(max(0.0, min(1.0, quality)))
        return GuardReport(df, quality, tier, usable, issues)
