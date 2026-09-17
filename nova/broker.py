from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from .db import Database
from .safety import SafetyEngine


@dataclass
class OrderResult:
    ok: bool
    message: str
    order_id: Optional[int] = None


class PaperBroker:
    def __init__(self, db: Database, safety: SafetyEngine):
        self.db = db
        self.safety = safety

    def portfolio_value(self, price_lookup: Optional[Callable[[str], float]] = None) -> float:
        value = self.db.get_cash()
        for pos in self.db.get_positions():
            price = float(pos["avg_price"])
            if price_lookup:
                try:
                    price = float(price_lookup(pos["ticker"]))
                except Exception:
                    pass
            value += int(pos["qty"]) * price
        return value

    def place_order(self, ticker: str, side: str, qty: int, price: float, source: str = "MANUAL") -> OrderResult:
        side = side.upper()
        qty = int(qty)
        price = float(price)
        position = self.db.get_position(ticker)
        held_qty = int(position["qty"]) if position else 0
        avg_price = float(position["avg_price"]) if position else 0.0
        current_position_value = held_qty * price

        portfolio_value = self.db.get_cash()
        for p in self.db.get_positions():
            mark = price if p["ticker"] == ticker else float(p["avg_price"])
            portfolio_value += int(p["qty"]) * mark

        safe = self.safety.check_order(
            ticker=ticker,
            side=side,
            qty=qty,
            price=price,
            portfolio_value=portfolio_value,
            current_position_value=current_position_value,
        )
        if not safe.allowed:
            order_id = self.db.add_order(ticker, side, qty, price, source, "BLOCKED", safe.reason)
            self.db.log(f"{ticker} {side} {qty}주 차단: {safe.reason}", "WARN")
            return OrderResult(False, safe.reason, order_id)

        total = price * qty
        cash = self.db.get_cash()

        if side == "BUY":
            if total > cash:
                reason = "모의계좌 현금이 부족합니다."
                order_id = self.db.add_order(ticker, side, qty, price, source, "REJECTED", reason)
                return OrderResult(False, reason, order_id)
            new_qty = held_qty + qty
            new_avg = ((held_qty * avg_price) + total) / new_qty
            self.db.set_cash(cash - total)
            self.db.upsert_position(ticker, new_qty, new_avg)
        elif side == "SELL":
            if qty > held_qty:
                reason = f"보유 수량({held_qty}주)보다 많이 매도할 수 없습니다."
                order_id = self.db.add_order(ticker, side, qty, price, source, "REJECTED", reason)
                return OrderResult(False, reason, order_id)
            new_qty = held_qty - qty
            self.db.set_cash(cash + total)
            self.db.upsert_position(ticker, new_qty, avg_price)
        else:
            return OrderResult(False, "지원하지 않는 주문 방향입니다.")

        order_id = self.db.add_order(ticker, side, qty, price, source, "FILLED", "paper fill")
        self.db.log(f"{ticker} {side} {qty}주 @ {price:,.2f} 모의체결 ({source})")
        return OrderResult(True, f"{ticker} {side} {qty}주가 {price:,.2f}에 모의체결되었습니다.", order_id)
