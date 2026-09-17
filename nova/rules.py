from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List

from .broker import PaperBroker
from .db import Database


@dataclass
class RuleEvent:
    rule_id: int
    ticker: str
    triggered: bool
    message: str


class RuleEngine:
    def __init__(self, db: Database, broker: PaperBroker):
        self.db = db
        self.broker = broker

    def scan(self, quote_lookup: Callable[[str], float]) -> List[RuleEvent]:
        events: List[RuleEvent] = []
        for rule in self.db.rules(enabled_only=True):
            ticker = rule["ticker"]
            try:
                price = float(quote_lookup(ticker))
            except Exception as e:
                events.append(RuleEvent(rule["id"], ticker, False, f"가격 조회 실패: {e}"))
                continue

            target = float(rule["trigger_price"])
            comparator = rule["comparator"]
            hit = price <= target if comparator == "<=" else price >= target
            if not hit:
                continue

            result = self.broker.place_order(
                ticker=ticker,
                side=rule["side"],
                qty=int(rule["qty"]),
                price=price,
                source=f"RULE#{rule['id']}",
            )
            if result.ok:
                self.db.mark_rule_triggered(int(rule["id"]))
            events.append(RuleEvent(int(rule["id"]), ticker, result.ok, result.message))
        return events
