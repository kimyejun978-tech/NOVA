from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Any

from .config import DB_PATH, DEFAULT_CASH, DEFAULT_COOLDOWN_SECONDS, DEFAULT_MAX_ORDER_VALUE, DEFAULT_MAX_POSITION_PCT


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


class Database:
    def __init__(self, path=DB_PATH):
        self.path = str(path)
        self._init_schema()

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS positions (
                    ticker TEXT PRIMARY KEY,
                    qty INTEGER NOT NULL,
                    avg_price REAL NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    side TEXT NOT NULL,
                    qty INTEGER NOT NULL,
                    price REAL NOT NULL,
                    total REAL NOT NULL,
                    source TEXT NOT NULL,
                    status TEXT NOT NULL,
                    reason TEXT
                );

                CREATE TABLE IF NOT EXISTS rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    comparator TEXT NOT NULL,
                    trigger_price REAL NOT NULL,
                    side TEXT NOT NULL,
                    qty INTEGER NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    last_trigger_at TEXT
                );

                CREATE TABLE IF NOT EXISTS activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL
                );
                """
            )

        defaults = {
            "cash": str(DEFAULT_CASH),
            "kill_switch": "0",
            "max_order_value": str(DEFAULT_MAX_ORDER_VALUE),
            "max_position_pct": str(DEFAULT_MAX_POSITION_PCT),
            "cooldown_seconds": str(DEFAULT_COOLDOWN_SECONDS),
        }
        for key, value in defaults.items():
            if self.get_setting(key) is None:
                self.set_setting(key, value)

    def get_setting(self, key: str, default: Any = None):
        with self.connect() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: Any) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO settings(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, str(value)),
            )

    def get_cash(self) -> float:
        return float(self.get_setting("cash", 0.0))

    def set_cash(self, cash: float) -> None:
        self.set_setting("cash", f"{cash:.8f}")

    def get_positions(self):
        with self.connect() as conn:
            return conn.execute("SELECT * FROM positions ORDER BY ticker").fetchall()

    def get_position(self, ticker: str):
        with self.connect() as conn:
            return conn.execute("SELECT * FROM positions WHERE ticker=?", (ticker,)).fetchone()

    def upsert_position(self, ticker: str, qty: int, avg_price: float) -> None:
        with self.connect() as conn:
            if qty <= 0:
                conn.execute("DELETE FROM positions WHERE ticker=?", (ticker,))
            else:
                conn.execute(
                    """
                    INSERT INTO positions(ticker, qty, avg_price, updated_at)
                    VALUES(?, ?, ?, ?)
                    ON CONFLICT(ticker) DO UPDATE SET
                        qty=excluded.qty,
                        avg_price=excluded.avg_price,
                        updated_at=excluded.updated_at
                    """,
                    (ticker, qty, avg_price, now_iso()),
                )

    def add_order(self, ticker: str, side: str, qty: int, price: float, source: str, status: str, reason: str = "") -> int:
        with self.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO orders(created_at, ticker, side, qty, price, total, source, status, reason)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (now_iso(), ticker, side, qty, price, price * qty, source, status, reason),
            )
            return int(cur.lastrowid)

    def recent_orders(self, limit: int = 50):
        with self.connect() as conn:
            return conn.execute("SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,)).fetchall()

    def last_filled_order_for_ticker(self, ticker: str):
        with self.connect() as conn:
            return conn.execute(
                """
                SELECT * FROM orders
                WHERE ticker=? AND status='FILLED'
                ORDER BY id DESC LIMIT 1
                """,
                (ticker,),
            ).fetchone()

    def add_rule(self, ticker: str, comparator: str, trigger_price: float, side: str, qty: int) -> int:
        with self.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO rules(ticker, comparator, trigger_price, side, qty, enabled, created_at)
                VALUES(?, ?, ?, ?, ?, 1, ?)
                """,
                (ticker, comparator, trigger_price, side, qty, now_iso()),
            )
            return int(cur.lastrowid)

    def rules(self, enabled_only: bool = False):
        sql = "SELECT * FROM rules"
        if enabled_only:
            sql += " WHERE enabled=1"
        sql += " ORDER BY id DESC"
        with self.connect() as conn:
            return conn.execute(sql).fetchall()

    def set_rule_enabled(self, rule_id: int, enabled: bool) -> None:
        with self.connect() as conn:
            conn.execute("UPDATE rules SET enabled=? WHERE id=?", (1 if enabled else 0, rule_id))

    def mark_rule_triggered(self, rule_id: int) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE rules SET enabled=0, last_trigger_at=? WHERE id=?",
                (now_iso(), rule_id),
            )

    def delete_rule(self, rule_id: int) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM rules WHERE id=?", (rule_id,))

    def log(self, message: str, level: str = "INFO") -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO activity(created_at, level, message) VALUES(?, ?, ?)",
                (now_iso(), level, message),
            )

    def recent_activity(self, limit: int = 100):
        with self.connect() as conn:
            return conn.execute("SELECT * FROM activity ORDER BY id DESC LIMIT ?", (limit,)).fetchall()

    def reset_paper_account(self) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM positions")
            conn.execute("DELETE FROM orders")
            conn.execute("DELETE FROM rules")
            conn.execute("DELETE FROM activity")
        self.set_cash(DEFAULT_CASH)
        self.set_setting("kill_switch", "0")
