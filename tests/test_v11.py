import numpy as np
import pandas as pd

from nova.data_guard import DataGuard
from nova.ml import HybridPredictor
from nova.updater import _version_tuple


def make_prices(n=1100, seed=1):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2021-01-01", periods=n)
    ret = 0.0003 + rng.normal(0, 0.012, n)
    close = 100 * np.cumprod(1 + ret)
    open_ = close * (1 + rng.normal(0, 0.002, n))
    high = np.maximum(open_, close) * 1.006
    low = np.minimum(open_, close) * 0.994
    return pd.DataFrame(
        {
            "Open": open_,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": rng.integers(100_000, 900_000, n),
        },
        index=idx,
    )


def test_data_guard_disables_short_stock_model():
    report = DataGuard().inspect(make_prices(220))
    assert report.tier == "GLOBAL_ONLY"
    assert not report.usable_for_stock_model


def test_hybrid_uses_stock_and_global_models():
    selected = DataGuard().inspect(make_prices(1100, 10))
    peers = {f"P{i}": make_prices(950 + i * 20, 20 + i) for i in range(4)}
    pred = HybridPredictor().predict(selected, peers, 5)
    assert pred.stock_probability is not None
    assert pred.global_probability is not None
    assert 0 <= pred.up_probability <= 1
    assert 0 <= pred.model_score <= 1


def test_version_compare_tuple():
    assert _version_tuple("v1.2.0") > _version_tuple("1.1.9")
