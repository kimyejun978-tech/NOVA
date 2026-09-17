from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .db import Database


@dataclass
class SafetyResult:
    allowed: bool
    reason: str = ""


class SafetyEngine:
    """Hard-coded guardrails. No ML/LLM component is allowed to bypass this class."""

    def __init__(self, db: Database):
        self.db = db

    def check_order(self, ticker: str, side: str, qty: int, price: float, portfolio_value: float, current_position_value: float) -> SafetyResult:
        if self.db.get_setting("kill_switch", "0") == "1":
            return SafetyResult(False, "Kill Switch가 켜져 있습니다.")
        if qty <= 0 or price <= 0:
            return SafetyResult(False, "수량과 가격은 0보다 커야 합니다.")

        order_value = qty * price
        max_order = float(self.db.get_setting("max_order_value", 2_000_000))
        if order_value > max_order:
            return SafetyResult(False, f"1회 최대 주문금액 {max_order:,.0f}원을 초과합니다.")

        if side == "BUY" and portfolio_value > 0:
            max_position_pct = float(self.db.get_setting("max_position_pct", 25.0)) / 100.0
            projected = current_position_value + order_value
            if projected / portfolio_value > max_position_pct:
                return SafetyResult(False, f"종목당 최대 비중 {max_position_pct * 100:.0f}%를 초과합니다.")

        last = self.db.last_filled_order_for_ticker(ticker)
        if last:
            cooldown = int(float(self.db.get_setting("cooldown_seconds", 60)))
            try:
                last_dt = datetime.fromisoformat(last["created_at"])
                elapsed = (datetime.now().astimezone() - last_dt).total_seconds()
                if elapsed < cooldown:
                    return SafetyResult(False, f"연속 주문 대기시간 {cooldown}초가 지나지 않았습니다.")
            except ValueError:
                pass

        return SafetyResult(True, "OK")
