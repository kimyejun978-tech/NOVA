from pathlib import Path
import tempfile

import numpy as np
import pandas as pd

from nova.db import Database
from nova.safety import SafetyEngine
from nova.broker import PaperBroker
from nova.ml import build_feature_frame


def make_prices(n=220):
    idx = pd.date_range("2025-01-01", periods=n, freq="B")
    close = 100 + np.cumsum(np.sin(np.arange(n) / 9) * 0.4 + 0.12)
    return pd.DataFrame({
        "Open": close - 0.3,
        "High": close + 1.0,
        "Low": close - 1.0,
        "Close": close,
        "Volume": 100000 + (np.arange(n) % 20) * 1500,
    }, index=idx)


def test_features_are_created():
    frame = build_feature_frame(make_prices(), 5)
    assert "rsi14" in frame.columns
    assert "future_return" in frame.columns
    assert frame["ret5"].notna().sum() > 100


def test_paper_buy_and_sell():
    with tempfile.TemporaryDirectory() as td:
        db = Database(Path(td) / "test.db")
        db.set_setting("max_position_pct", 100)
        db.set_setting("cooldown_seconds", 0)
        broker = PaperBroker(db, SafetyEngine(db))
        buy = broker.place_order("TEST", "BUY", 10, 1000, "TEST")
        assert buy.ok
        assert db.get_position("TEST")["qty"] == 10
        sell = broker.place_order("TEST", "SELL", 5, 1100, "TEST")
        assert sell.ok
        assert db.get_position("TEST")["qty"] == 5
