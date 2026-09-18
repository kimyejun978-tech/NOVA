import numpy as np
import pandas as pd

import nova.recommender as recommender
from nova.recommender import RecommendationEngine, _ranking_score


def make_prices(n=340, seed=1, drift=0.0006):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2024-01-01", periods=n)
    ret = drift + rng.normal(0, 0.008, n)
    close = 100 * np.cumprod(1 + ret)
    open_ = close * (1 + rng.normal(0, 0.0015, n))
    high = np.maximum(open_, close) * 1.004
    low = np.minimum(open_, close) * 0.996
    return pd.DataFrame(
        {
            "Open": open_,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": rng.integers(150_000, 900_000, n),
        },
        index=idx,
    )


class FakeModel:
    def fit(self, X, y):
        return self

    def predict_proba(self, X):
        # Deterministic but feature-driven probabilities for fast CI tests.
        ret20 = np.asarray(X["ret20"], dtype=float)
        ret5 = np.asarray(X["ret5"], dtype=float)
        p = np.clip(0.58 + ret20 * 1.8 + ret5 * 0.8, 0.08, 0.92)
        return np.column_stack([1.0 - p, p])


class FakeMarket:
    def __init__(self):
        self.data = {
            "AAA": make_prices(seed=1, drift=0.0008),
            "BBB": make_prices(seed=2, drift=0.0005),
            "CCC": make_prices(seed=3, drift=0.0007),
            "DDD": make_prices(seed=4, drift=0.0004),
        }

    def history(self, ticker, period="5y", interval="1d"):
        if ticker not in self.data:
            raise RuntimeError("not available")
        return self.data[ticker].copy()


def test_ranking_score_rewards_stronger_signal():
    strong = _ranking_score(0.72, 0.75, 0.95, 0.90)
    weak = _ranking_score(0.54, 0.45, 0.75, 0.55)
    assert strong > weak
    assert 0 <= weak <= 100
    assert 0 <= strong <= 100


def test_recommender_returns_ranked_research_candidates(monkeypatch):
    monkeypatch.setattr(
        recommender,
        "KOREA_SCAN_UNIVERSE",
        [("AAA", "A"), ("BBB", "B"), ("CCC", "C"), ("DDD", "D")],
    )
    monkeypatch.setattr(recommender, "_model", lambda seed, trees=260: FakeModel())

    result = RecommendationEngine(FakeMarket()).scan(
        market_code="KR",
        horizon_days=5,
        limit=3,
        min_confidence=0.0,
    )

    assert result.scanned == 4
    assert result.usable == 4
    assert 1 <= len(result.candidates) <= 3
    assert all(0 <= x.up_probability <= 1 for x in result.candidates)
    assert all(0 <= x.confidence <= 1 for x in result.candidates)
    scores = [x.score for x in result.candidates]
    assert scores == sorted(scores, reverse=True)
