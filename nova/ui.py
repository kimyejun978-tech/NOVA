from __future__ import annotations

from functools import partial
from typing import Any, Callable

import pandas as pd
from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtGui import QPainter

from .advisor import Advisor
from .analysis_engine import AnalysisEngine, AnalysisResult
from .broker import PaperBroker
from .config import APP_NAME, APP_VERSION, AUTO_SCAN_SECONDS, UPDATE_DIR
from .db import Database
from .market import YahooMarketData, normalize_ticker
from .ml import Prediction
from .updater import UpdateInfo, check_latest, stage_update
from .rules import RuleEngine
from .safety import SafetyEngine


STYLE = """
QMainWindow, QWidget {
    background: #0b0f14;
    color: #e8edf3;
    font-family: "Segoe UI", "Malgun Gothic";
    font-size: 13px;
}
QFrame#Sidebar { background: #090c10; border-right: 1px solid #1b2430; }
QFrame#Card { background: #111821; border: 1px solid #202b38; border-radius: 12px; }
QLabel#Brand { font-size: 25px; font-weight: 800; letter-spacing: 2px; }
QLabel#Muted { color: #8190a3; }
QLabel#Hero { font-size: 26px; font-weight: 800; }
QLabel#Metric { font-size: 22px; font-weight: 750; }
QLabel#Section { font-size: 17px; font-weight: 700; }
QPushButton {
    background: #182230; border: 1px solid #2a3849; border-radius: 8px;
    padding: 9px 13px; color: #e8edf3;
}
QPushButton:hover { background: #202d3d; }
QPushButton:pressed { background: #111923; }
QPushButton#Primary { background: #2f6feb; border-color: #2f6feb; font-weight: 700; }
QPushButton#Primary:hover { background: #3d7bf2; }
QPushButton#Danger { background: #552126; border-color: #7a3038; font-weight: 700; }
QPushButton#Danger:checked { background: #a32d3a; border-color: #d1424f; }
QPushButton#Nav { text-align: left; border: none; background: transparent; padding: 11px 14px; }
QPushButton#Nav:hover { background: #121a24; }
QPushButton#Nav:checked { background: #172231; border-left: 3px solid #4c8dff; }
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit {
    background: #0d131b; border: 1px solid #273445; border-radius: 8px; padding: 8px;
    selection-background-color: #2f6feb;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QTextEdit:focus { border-color: #4c8dff; }
QTableWidget { background: #0d131b; border: 1px solid #202b38; border-radius: 8px; gridline-color: #1d2733; }
QHeaderView::section { background: #141c26; color: #9eacbd; border: none; border-bottom: 1px solid #273445; padding: 8px; }
QTableWidget::item { padding: 6px; }
QTableWidget::item:selected { background: #1f3d69; }
QCheckBox { spacing: 8px; }
"""


class TaskThread(QThread):
    done = Signal(object)
    failed = Signal(str)

    def __init__(self, fn: Callable[[], Any], parent=None):
        super().__init__(parent)
        self.fn = fn

    def run(self):
        try:
            self.done.emit(self.fn())
        except Exception as e:
            self.failed.emit(str(e))


def card() -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("Card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(8)
    return frame, layout


def section_title(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("Section")
    return label


def item(text: Any) -> QTableWidgetItem:
    x = QTableWidgetItem(str(text))
    x.setFlags(x.flags() & ~Qt.ItemFlag.ItemIsEditable)
    return x


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.market = YahooMarketData()
        self.analysis_engine = AnalysisEngine(self.market)
        self.safety = SafetyEngine(self.db)
        self.broker = PaperBroker(self.db, self.safety)
        self.rules = RuleEngine(self.db, self.broker)
        self.advisor = Advisor()

        self._threads: list[TaskThread] = []
        self.current_quote = None
        self.current_analysis: AnalysisResult | None = None
        self.latest_update: UpdateInfo | None = None
        self.analysis_easy = True
        self.rule_scan_running = False

        self.setWindowTitle(f"{APP_NAME} — Paper Trading v{APP_VERSION}")
        self.resize(1280, 820)
        self.setMinimumSize(1050, 700)
        self.setStyleSheet(STYLE)
        self._build_ui()
        self._build_menu()
        self.refresh_all()

        self.scan_timer = QTimer(self)
        self.scan_timer.timeout.connect(self.scan_rules_async)
        self.scan_timer.start(AUTO_SCAN_SECONDS * 1000)
        QTimer.singleShot(2500, self.check_updates_silent)

    def _build_menu(self):
        menu = self.menuBar().addMenu("NOVA")
        refresh = QAction("새로고침", self)
        refresh.triggered.connect(self.refresh_all)
        menu.addAction(refresh)
        check_update = QAction("업데이트 확인", self)
        check_update.triggered.connect(lambda: self.check_updates_silent(show_current=True))
        menu.addAction(check_update)

    def _build_ui(self):
        root = QWidget()
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(205)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(14, 18, 14, 14)
        side.setSpacing(5)

        brand = QLabel("NOVA")
        brand.setObjectName("Brand")
        sub = QLabel("PAPER INTELLIGENCE")
        sub.setObjectName("Muted")
        side.addWidget(brand)
        side.addWidget(sub)
        side.addSpacing(18)

        self.nav_buttons = []
        pages = [
            ("Overview", self._make_dashboard()),
            ("Analyze", self._make_analysis()),
            ("Paper Trade", self._make_trade()),
            ("Rules", self._make_rules()),
            ("Safety", self._make_safety()),
            ("Updates", self._make_updates()),
        ]
        self.stack = QStackedWidget()
        for idx, (name, page) in enumerate(pages):
            b = QPushButton(name)
            b.setObjectName("Nav")
            b.setCheckable(True)
            b.clicked.connect(partial(self._switch_page, idx))
            self.nav_buttons.append(b)
            side.addWidget(b)
            self.stack.addWidget(page)
        self.nav_buttons[0].setChecked(True)

        side.addStretch(1)
        self.kill_badge = QLabel("Safety: checking…")
        self.kill_badge.setObjectName("Muted")
        side.addWidget(self.kill_badge)
        version = QLabel(f"v{APP_VERSION} · simulation only")
        version.setObjectName("Muted")
        side.addWidget(version)

        content = QWidget()
        c = QVBoxLayout(content)
        c.setContentsMargins(24, 18, 24, 18)
        c.addWidget(self.stack)

        outer.addWidget(sidebar)
        outer.addWidget(content, 1)
        self.setCentralWidget(root)
        self.statusBar().showMessage("NOVA ready · 실제 주문 기능 없음")

    def _switch_page(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, b in enumerate(self.nav_buttons):
            b.setChecked(i == index)
        if index in (0, 2, 3, 4):
            self.refresh_all()

    def _make_dashboard(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setSpacing(14)
        title = QLabel("Paper portfolio")
        title.setObjectName("Hero")
        lay.addWidget(title)
        desc = QLabel("실계좌와 분리된 모의 자동매매 환경입니다. 네트워크 가격 데이터는 지연될 수 있습니다.")
        desc.setObjectName("Muted")
        lay.addWidget(desc)

        metrics = QHBoxLayout()
        self.cash_card, cash_l = card()
        cash_l.addWidget(QLabel("Cash"))
        self.cash_value = QLabel("-")
        self.cash_value.setObjectName("Metric")
        cash_l.addWidget(self.cash_value)
        metrics.addWidget(self.cash_card)

        self.asset_card, asset_l = card()
        asset_l.addWidget(QLabel("Book value"))
        self.asset_value = QLabel("-")
        self.asset_value.setObjectName("Metric")
        asset_l.addWidget(self.asset_value)
        metrics.addWidget(self.asset_card)

        self.pos_card, pos_l = card()
        pos_l.addWidget(QLabel("Positions"))
        self.pos_value = QLabel("-")
        self.pos_value.setObjectName("Metric")
        pos_l.addWidget(self.pos_value)
        metrics.addWidget(self.pos_card)
        lay.addLayout(metrics)

        lay.addWidget(section_title("Positions"))
        self.positions_table = QTableWidget(0, 5)
        self.positions_table.setHorizontalHeaderLabels(["Ticker", "Qty", "Avg", "Book value", "Updated"])
        self._setup_table(self.positions_table)
        lay.addWidget(self.positions_table, 1)

        lay.addWidget(section_title("Recent orders"))
        self.orders_table = QTableWidget(0, 7)
        self.orders_table.setHorizontalHeaderLabels(["Time", "Ticker", "Side", "Qty", "Price", "Source", "Status"])
        self._setup_table(self.orders_table)
        lay.addWidget(self.orders_table, 1)
        return page

    def _make_analysis(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setSpacing(12)
        title = QLabel("Analyze")
        title.setObjectName("Hero")
        lay.addWidget(title)
        subtitle = QLabel("선택 종목을 집중 학습하는 Stock Model과 여러 종목을 학습한 Global Model을 결합합니다. Data Guard가 비정상·부족 데이터를 먼저 검사합니다.")
        subtitle.setObjectName("Muted")
        lay.addWidget(subtitle)

        top = QHBoxLayout()
        self.analysis_ticker = QLineEdit()
        self.analysis_ticker.setPlaceholderText("005930.KS / 000660.KS / AAPL / 삼성전자")
        top.addWidget(self.analysis_ticker, 3)
        self.horizon = QComboBox()
        self.horizon.addItem("1 day", 1)
        self.horizon.addItem("1 week", 5)
        self.horizon.addItem("1 month", 20)
        self.horizon.setCurrentIndex(1)
        top.addWidget(self.horizon, 1)
        self.analyze_btn = QPushButton("Run analysis")
        self.analyze_btn.setObjectName("Primary")
        self.analyze_btn.clicked.connect(self.run_analysis)
        top.addWidget(self.analyze_btn)
        lay.addLayout(top)

        toggle = QHBoxLayout()
        self.easy_btn = QPushButton("Easy view")
        self.detail_btn = QPushButton("Detailed view")
        self.easy_btn.setCheckable(True)
        self.detail_btn.setCheckable(True)
        self.easy_btn.setChecked(True)
        self.easy_btn.clicked.connect(lambda: self.set_analysis_view(True))
        self.detail_btn.clicked.connect(lambda: self.set_analysis_view(False))
        toggle.addWidget(self.easy_btn)
        toggle.addWidget(self.detail_btn)
        toggle.addStretch(1)
        lay.addLayout(toggle)

        metric_row = QHBoxLayout()
        c1, l1 = card(); l1.addWidget(QLabel("UP probability")); self.up_label = QLabel("-"); self.up_label.setObjectName("Metric"); l1.addWidget(self.up_label); metric_row.addWidget(c1)
        c2, l2 = card(); l2.addWidget(QLabel("Reference range")); self.range_label = QLabel("-"); self.range_label.setObjectName("Metric"); l2.addWidget(self.range_label); metric_row.addWidget(c2)
        c3, l3 = card(); l3.addWidget(QLabel("Confidence")); self.conf_label = QLabel("-"); self.conf_label.setObjectName("Metric"); l3.addWidget(self.conf_label); metric_row.addWidget(c3)
        c4, l4 = card(); l4.addWidget(QLabel("Data tier")); self.tier_label = QLabel("-"); self.tier_label.setObjectName("Metric"); l4.addWidget(self.tier_label); metric_row.addWidget(c4)
        lay.addLayout(metric_row)

        bottom = QHBoxLayout()
        left_card, left_l = card()
        left_l.addWidget(section_title("AI advisory"))
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setMinimumHeight(190)
        left_l.addWidget(self.analysis_text)
        self.rule_advice = QLabel("분석 후 전략 권고가 표시됩니다.")
        self.rule_advice.setWordWrap(True)
        self.rule_advice.setObjectName("Muted")
        left_l.addWidget(self.rule_advice)
        bottom.addWidget(left_card, 2)

        self.chart_card, chart_l = card()
        chart_l.addWidget(section_title("Price / SMA20"))
        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.chart_view.setMinimumHeight(280)
        chart_l.addWidget(self.chart_view)
        bottom.addWidget(self.chart_card, 3)
        lay.addLayout(bottom, 1)
        self.chart_card.setVisible(False)
        return page

    def _make_trade(self):
        page = QWidget(); lay = QVBoxLayout(page); lay.setSpacing(14)
        title = QLabel("Paper trade"); title.setObjectName("Hero"); lay.addWidget(title)
        desc = QLabel("실제 증권사 주문 코드는 포함하지 않습니다. 표시 가격으로 모의 체결만 합니다."); desc.setObjectName("Muted"); lay.addWidget(desc)

        c, cl = card()
        form = QGridLayout()
        self.trade_ticker = QLineEdit(); self.trade_ticker.setPlaceholderText("005930.KS / AAPL")
        self.quote_btn = QPushButton("Get price"); self.quote_btn.clicked.connect(self.fetch_trade_quote)
        self.trade_price = QLabel("No quote"); self.trade_price.setObjectName("Metric")
        self.trade_qty = QSpinBox(); self.trade_qty.setRange(1, 1_000_000); self.trade_qty.setValue(1)
        self.buy_btn = QPushButton("BUY (paper)"); self.buy_btn.setObjectName("Primary"); self.buy_btn.clicked.connect(lambda: self.place_manual("BUY"))
        self.sell_btn = QPushButton("SELL (paper)"); self.sell_btn.clicked.connect(lambda: self.place_manual("SELL"))
        form.addWidget(QLabel("Ticker"), 0, 0); form.addWidget(self.trade_ticker, 0, 1); form.addWidget(self.quote_btn, 0, 2)
        form.addWidget(QLabel("Last price"), 1, 0); form.addWidget(self.trade_price, 1, 1, 1, 2)
        form.addWidget(QLabel("Quantity"), 2, 0); form.addWidget(self.trade_qty, 2, 1, 1, 2)
        form.addWidget(self.buy_btn, 3, 1); form.addWidget(self.sell_btn, 3, 2)
        cl.addLayout(form); lay.addWidget(c)

        lay.addWidget(section_title("Order history"))
        self.trade_orders = QTableWidget(0, 8)
        self.trade_orders.setHorizontalHeaderLabels(["Time", "Ticker", "Side", "Qty", "Price", "Total", "Source", "Status"])
        self._setup_table(self.trade_orders)
        lay.addWidget(self.trade_orders, 1)
        return page

    def _make_rules(self):
        page = QWidget(); lay = QVBoxLayout(page); lay.setSpacing(12)
        title = QLabel("Rules"); title.setObjectName("Hero"); lay.addWidget(title)
        d = QLabel("사용자가 만든 가격 규칙만 자동 실행됩니다. AI는 이 테이블을 생성·수정·삭제하지 못합니다. v1 규칙은 성공 체결 후 자동 비활성화됩니다."); d.setObjectName("Muted"); d.setWordWrap(True); lay.addWidget(d)

        c, cl = card(); grid = QGridLayout()
        self.rule_ticker = QLineEdit(); self.rule_ticker.setPlaceholderText("005930.KS")
        self.rule_comp = QComboBox(); self.rule_comp.addItem("price <=", "<="); self.rule_comp.addItem("price >=", ">=")
        self.rule_price = QDoubleSpinBox(); self.rule_price.setRange(0.01, 1_000_000_000); self.rule_price.setDecimals(2); self.rule_price.setValue(70000)
        self.rule_side = QComboBox(); self.rule_side.addItems(["BUY", "SELL"])
        self.rule_qty = QSpinBox(); self.rule_qty.setRange(1, 1_000_000); self.rule_qty.setValue(1)
        add = QPushButton("Add one-shot rule"); add.setObjectName("Primary"); add.clicked.connect(self.add_rule)
        scan = QPushButton("Scan now"); scan.clicked.connect(self.scan_rules_async)
        grid.addWidget(QLabel("Ticker"), 0, 0); grid.addWidget(self.rule_ticker, 0, 1)
        grid.addWidget(QLabel("Condition"), 0, 2); grid.addWidget(self.rule_comp, 0, 3)
        grid.addWidget(QLabel("Trigger price"), 1, 0); grid.addWidget(self.rule_price, 1, 1)
        grid.addWidget(QLabel("Action"), 1, 2); grid.addWidget(self.rule_side, 1, 3)
        grid.addWidget(QLabel("Qty"), 2, 0); grid.addWidget(self.rule_qty, 2, 1)
        grid.addWidget(add, 2, 2); grid.addWidget(scan, 2, 3)
        cl.addLayout(grid); lay.addWidget(c)

        self.rule_status = QLabel(f"Auto scan: every {AUTO_SCAN_SECONDS}s")
        self.rule_status.setObjectName("Muted"); lay.addWidget(self.rule_status)
        self.rules_table = QTableWidget(0, 8)
        self.rules_table.setHorizontalHeaderLabels(["ID", "Ticker", "Condition", "Price", "Side", "Qty", "Enabled", "Last trigger"])
        self._setup_table(self.rules_table)
        self.rules_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        lay.addWidget(self.rules_table, 1)
        actions = QHBoxLayout()
        toggle = QPushButton("Enable / Disable selected"); toggle.clicked.connect(self.toggle_selected_rule)
        delete = QPushButton("Delete selected"); delete.clicked.connect(self.delete_selected_rule)
        actions.addWidget(toggle); actions.addWidget(delete); actions.addStretch(1); lay.addLayout(actions)
        return page

    def _make_safety(self):
        page = QWidget(); lay = QVBoxLayout(page); lay.setSpacing(14)
        title = QLabel("Safety engine"); title.setObjectName("Hero"); lay.addWidget(title)
        d = QLabel("ML/AI 계층과 분리된 하드 제한입니다. 모의 주문과 자동 규칙 모두 이 검사를 통과해야 합니다."); d.setObjectName("Muted"); lay.addWidget(d)

        kill_card, kl = card()
        self.kill_switch = QPushButton("KILL SWITCH — block every new order")
        self.kill_switch.setObjectName("Danger"); self.kill_switch.setCheckable(True); self.kill_switch.clicked.connect(self.set_kill_switch)
        kl.addWidget(self.kill_switch)
        note = QLabel("켜져 있어도 기존 모의 보유수량은 삭제하지 않습니다. 신규 BUY/SELL 체결만 차단합니다."); note.setObjectName("Muted"); kl.addWidget(note)
        lay.addWidget(kill_card)

        lim_card, ll = card(); grid = QGridLayout()
        self.max_order = QDoubleSpinBox(); self.max_order.setRange(1_000, 1_000_000_000); self.max_order.setDecimals(0); self.max_order.setSuffix(" KRW")
        self.max_pos = QDoubleSpinBox(); self.max_pos.setRange(1, 100); self.max_pos.setDecimals(1); self.max_pos.setSuffix(" %")
        self.cooldown = QSpinBox(); self.cooldown.setRange(0, 86_400); self.cooldown.setSuffix(" sec")
        save = QPushButton("Save limits"); save.setObjectName("Primary"); save.clicked.connect(self.save_safety)
        grid.addWidget(QLabel("Max order value"), 0, 0); grid.addWidget(self.max_order, 0, 1)
        grid.addWidget(QLabel("Max position weight"), 1, 0); grid.addWidget(self.max_pos, 1, 1)
        grid.addWidget(QLabel("Same ticker cooldown"), 2, 0); grid.addWidget(self.cooldown, 2, 1)
        grid.addWidget(save, 3, 1)
        ll.addLayout(grid); lay.addWidget(lim_card)

        reset_card, rl = card(); rl.addWidget(section_title("Reset simulation"))
        rn = QLabel("모의잔고·포지션·주문·규칙을 모두 초기화하고 현금 10,000,000원으로 되돌립니다."); rn.setObjectName("Muted"); rl.addWidget(rn)
        reset = QPushButton("Reset paper account"); reset.clicked.connect(self.reset_account); rl.addWidget(reset)
        lay.addWidget(reset_card); lay.addStretch(1)
        return page

    def _make_updates(self):
        page = QWidget(); lay = QVBoxLayout(page); lay.setSpacing(14)
        title = QLabel("Updates"); title.setObjectName("Hero"); lay.addWidget(title)
        d = QLabel("시작할 때 GitHub Release를 자동 확인합니다. 업데이트 파일은 SHA-256 검증 후 별도 updater가 NOVA를 종료·교체·재시작합니다. 모의계좌 DB는 LOCALAPPDATA에 있어 유지됩니다.")
        d.setObjectName("Muted"); d.setWordWrap(True); lay.addWidget(d)

        c, cl = card()
        cl.addWidget(section_title("NOVA Update"))
        self.update_current = QLabel(f"Current version: {APP_VERSION}")
        self.update_status = QLabel("아직 업데이트를 확인하지 않았습니다.")
        self.update_status.setWordWrap(True)
        self.update_status.setObjectName("Muted")
        self.update_notes = QTextEdit(); self.update_notes.setReadOnly(True); self.update_notes.setMinimumHeight(180)
        row = QHBoxLayout()
        check = QPushButton("Check for updates"); check.clicked.connect(lambda: self.check_updates_silent(show_current=True))
        self.install_update_btn = QPushButton("Update & restart"); self.install_update_btn.setObjectName("Primary")
        self.install_update_btn.setEnabled(False); self.install_update_btn.clicked.connect(self.install_update)
        row.addWidget(check); row.addWidget(self.install_update_btn); row.addStretch(1)
        cl.addWidget(self.update_current); cl.addWidget(self.update_status); cl.addWidget(self.update_notes); cl.addLayout(row)
        lay.addWidget(c); lay.addStretch(1)
        return page

    def _setup_table(self, table: QTableWidget):
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setAlternatingRowColors(False)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

    def run_task(self, fn: Callable[[], Any], done: Callable[[Any], None], failed: Callable[[str], None] | None = None):
        thread = TaskThread(fn, self)
        self._threads.append(thread)
        def cleanup():
            if thread in self._threads:
                self._threads.remove(thread)
            thread.deleteLater()
        thread.done.connect(done)
        thread.done.connect(lambda _: cleanup())
        thread.failed.connect(failed or self.show_error)
        thread.failed.connect(lambda _: cleanup())
        thread.start()

    def show_error(self, message: str):
        self.statusBar().showMessage(f"Error: {message}")
        QMessageBox.warning(self, "NOVA", message)

    def refresh_all(self):
        self.refresh_dashboard()
        self.refresh_orders()
        self.refresh_rules()
        self.refresh_safety()

    def refresh_dashboard(self):
        cash = self.db.get_cash()
        positions = self.db.get_positions()
        book = cash + sum(int(p["qty"]) * float(p["avg_price"]) for p in positions)
        self.cash_value.setText(f"₩{cash:,.0f}")
        self.asset_value.setText(f"₩{book:,.0f}")
        self.pos_value.setText(str(len(positions)))
        self.positions_table.setRowCount(len(positions))
        for r, p in enumerate(positions):
            vals = [p["ticker"], p["qty"], f"{p['avg_price']:,.2f}", f"{p['qty'] * p['avg_price']:,.0f}", p["updated_at"]]
            for c, v in enumerate(vals): self.positions_table.setItem(r, c, item(v))

        orders = self.db.recent_orders(12)
        self.orders_table.setRowCount(len(orders))
        for r, o in enumerate(orders):
            vals = [o["created_at"], o["ticker"], o["side"], o["qty"], f"{o['price']:,.2f}", o["source"], o["status"]]
            for c, v in enumerate(vals): self.orders_table.setItem(r, c, item(v))

    def refresh_orders(self):
        if not hasattr(self, "trade_orders"): return
        orders = self.db.recent_orders(80)
        self.trade_orders.setRowCount(len(orders))
        for r, o in enumerate(orders):
            vals = [o["created_at"], o["ticker"], o["side"], o["qty"], f"{o['price']:,.2f}", f"{o['total']:,.0f}", o["source"], o["status"]]
            for c, v in enumerate(vals): self.trade_orders.setItem(r, c, item(v))

    def refresh_rules(self):
        if not hasattr(self, "rules_table"): return
        rules = self.db.rules()
        self.rules_table.setRowCount(len(rules))
        for r, x in enumerate(rules):
            vals = [x["id"], x["ticker"], x["comparator"], f"{x['trigger_price']:,.2f}", x["side"], x["qty"], "ON" if x["enabled"] else "OFF", x["last_trigger_at"] or "-"]
            for c, v in enumerate(vals): self.rules_table.setItem(r, c, item(v))

    def refresh_safety(self):
        if not hasattr(self, "kill_switch"): return
        on = self.db.get_setting("kill_switch", "0") == "1"
        self.kill_switch.blockSignals(True); self.kill_switch.setChecked(on); self.kill_switch.blockSignals(False)
        self.kill_switch.setText("KILL SWITCH ON — every new order blocked" if on else "KILL SWITCH OFF — paper orders allowed")
        self.kill_badge.setText("Safety: KILL SWITCH ON" if on else "Safety: armed")
        self.max_order.setValue(float(self.db.get_setting("max_order_value", 2_000_000)))
        self.max_pos.setValue(float(self.db.get_setting("max_position_pct", 25)))
        self.cooldown.setValue(int(float(self.db.get_setting("cooldown_seconds", 60))))

    def run_analysis(self):
        raw = self.analysis_ticker.text().strip()
        if not raw:
            self.show_error("분석할 종목을 입력하세요."); return
        try: ticker = normalize_ticker(raw)
        except Exception as e: self.show_error(str(e)); return
        horizon = int(self.horizon.currentData())
        self.analyze_btn.setEnabled(False); self.analyze_btn.setText("Analyzing…")
        self.statusBar().showMessage(f"{ticker} · Data Guard → Stock ML → Global ML → Ensemble 분석 중…")

        def task():
            return self.analysis_engine.analyze(ticker, horizon_days=horizon)

        def done(result):
            self.analyze_btn.setEnabled(True); self.analyze_btn.setText("Run analysis")
            self.current_analysis = result
            self.render_analysis()
            warnings = sum(1 for x in result.guard.issues if x.severity in ("WARN", "BLOCK"))
            self.statusBar().showMessage(f"{result.ticker} 분석 완료 · market datasets {result.market_dataset_count} · data warnings {warnings}")

        def failed(msg):
            self.analyze_btn.setEnabled(True); self.analyze_btn.setText("Run analysis")
            self.show_error(msg)
        self.run_task(task, done, failed)

    def set_analysis_view(self, easy: bool):
        self.analysis_easy = easy
        self.easy_btn.setChecked(easy); self.detail_btn.setChecked(not easy)
        self.chart_card.setVisible(not easy)
        self.render_analysis()

    def render_analysis(self):
        if not self.current_analysis: return
        result = self.current_analysis
        ticker, p, data = result.ticker, result.prediction, result.data
        self.up_label.setText(f"{p.up_probability * 100:.1f}%")
        self.range_label.setText(f"{p.expected_low_price:,.0f} ~ {p.expected_high_price:,.0f}")
        self.conf_label.setText(f"{p.model_score * 100:.0f}/100")
        self.tier_label.setText(p.data_tier)
        text = self.advisor.explain(ticker, p, easy=self.analysis_easy)
        if not self.analysis_easy and result.guard.issues:
            text += "\n\nData Guard:\n" + "\n".join(f"- [{x.severity}] {x.message}" for x in result.guard.issues)
        self.analysis_text.setPlainText(text)
        self.rule_advice.setText(self.advisor.rule_advice(p, p.current_price))
        if not self.analysis_easy:
            self.draw_chart(data)

    def draw_chart(self, data: pd.DataFrame):
        frame = data.tail(100).copy()
        close = frame["Close"].astype(float)
        sma20 = close.rolling(20).mean()
        chart = QChart(); chart.setBackgroundVisible(False); chart.setPlotAreaBackgroundVisible(False)
        chart.legend().setVisible(True); chart.legend().setLabelColor(Qt.GlobalColor.lightGray)
        close_s = QLineSeries(); close_s.setName("Close")
        sma_s = QLineSeries(); sma_s.setName("SMA20")
        for i, v in enumerate(close): close_s.append(i, float(v))
        for i, v in enumerate(sma20):
            if pd.notna(v): sma_s.append(i, float(v))
        chart.addSeries(close_s); chart.addSeries(sma_s)
        x = QValueAxis(); x.setRange(0, max(1, len(frame)-1)); x.setLabelsColor(Qt.GlobalColor.gray); x.setGridLineColor(Qt.GlobalColor.darkGray); x.setTitleText("recent trading days"); x.setTitleBrush(Qt.GlobalColor.gray)
        y = QValueAxis(); mn = float(close.min()) * 0.98; mx = float(close.max()) * 1.02; y.setRange(mn, mx); y.setLabelFormat("%.0f"); y.setLabelsColor(Qt.GlobalColor.gray); y.setGridLineColor(Qt.GlobalColor.darkGray)
        chart.addAxis(x, Qt.AlignmentFlag.AlignBottom); chart.addAxis(y, Qt.AlignmentFlag.AlignLeft)
        close_s.attachAxis(x); close_s.attachAxis(y); sma_s.attachAxis(x); sma_s.attachAxis(y)
        self.chart_view.setChart(chart)

    def fetch_trade_quote(self):
        raw = self.trade_ticker.text().strip()
        if not raw: self.show_error("종목을 입력하세요."); return
        try: ticker = normalize_ticker(raw)
        except Exception as e: self.show_error(str(e)); return
        self.quote_btn.setEnabled(False); self.trade_price.setText("Loading…")
        self.run_task(lambda: self.market.quote(ticker), self._quote_done, self._quote_failed)

    def _quote_done(self, q):
        self.quote_btn.setEnabled(True); self.current_quote = q
        self.trade_ticker.setText(q.ticker); self.trade_price.setText(f"{q.price:,.2f}  ·  {q.timestamp}")
        self.statusBar().showMessage(f"{q.ticker} quote loaded")

    def _quote_failed(self, msg):
        self.quote_btn.setEnabled(True); self.trade_price.setText("No quote"); self.show_error(msg)

    def place_manual(self, side: str):
        if not self.current_quote:
            self.show_error("먼저 Get price로 가격을 불러오세요."); return
        ticker = normalize_ticker(self.trade_ticker.text())
        if ticker != self.current_quote.ticker:
            self.show_error("종목 입력이 마지막으로 불러온 가격과 다릅니다. 가격을 다시 조회하세요."); return
        result = self.broker.place_order(ticker, side, self.trade_qty.value(), self.current_quote.price, "MANUAL")
        QMessageBox.information(self, "Paper order", result.message) if result.ok else QMessageBox.warning(self, "Paper order", result.message)
        self.refresh_all()

    def add_rule(self):
        try:
            ticker = normalize_ticker(self.rule_ticker.text())
            rid = self.db.add_rule(ticker, self.rule_comp.currentData(), self.rule_price.value(), self.rule_side.currentText(), self.rule_qty.value())
            self.db.log(f"Rule#{rid} created: {ticker} {self.rule_comp.currentData()} {self.rule_price.value()} -> {self.rule_side.currentText()} {self.rule_qty.value()}주")
            self.refresh_rules(); self.statusBar().showMessage(f"Rule#{rid} added")
        except Exception as e: self.show_error(str(e))

    def selected_rule_id(self):
        row = self.rules_table.currentRow()
        if row < 0: return None
        return int(self.rules_table.item(row, 0).text())

    def toggle_selected_rule(self):
        rid = self.selected_rule_id()
        if rid is None: self.show_error("규칙을 선택하세요."); return
        row = self.rules_table.currentRow(); enabled = self.rules_table.item(row, 6).text() == "ON"
        self.db.set_rule_enabled(rid, not enabled); self.refresh_rules()

    def delete_selected_rule(self):
        rid = self.selected_rule_id()
        if rid is None: self.show_error("규칙을 선택하세요."); return
        self.db.delete_rule(rid); self.refresh_rules()

    def scan_rules_async(self):
        if self.rule_scan_running or not self.db.rules(enabled_only=True): return
        self.rule_scan_running = True; self.rule_status.setText("Auto scan: checking prices…")
        def quote_lookup(ticker: str) -> float: return self.market.quote(ticker).price
        def task(): return self.rules.scan(quote_lookup)
        def done(events):
            self.rule_scan_running = False
            triggered = [e for e in events if e.triggered]
            self.rule_status.setText(f"Auto scan: every {AUTO_SCAN_SECONDS}s · last scan complete · fills {len(triggered)}")
            if events:
                for e in events: self.db.log(f"Rule#{e.rule_id}: {e.message}", "INFO" if e.triggered else "WARN")
            self.refresh_all()
        def failed(msg):
            self.rule_scan_running = False; self.rule_status.setText(f"Auto scan error: {msg}")
        self.run_task(task, done, failed)

    def check_updates_silent(self, show_current: bool = False):
        if hasattr(self, "update_status"):
            self.update_status.setText("업데이트 확인 중…")
        def done(info):
            self.latest_update = info
            if hasattr(self, "install_update_btn"):
                self.install_update_btn.setEnabled(bool(info.available and info.download_url))
                self.update_notes.setPlainText(info.notes or "Release notes 없음")
                if info.available:
                    self.update_status.setText(f"새 버전 {info.version} 사용 가능 · 현재 {APP_VERSION}")
                else:
                    self.update_status.setText(f"최신 버전입니다. ({APP_VERSION})")
            if info.available:
                self.statusBar().showMessage(f"NOVA {info.version} 업데이트 사용 가능")
            elif show_current:
                QMessageBox.information(self, "NOVA Update", f"현재 v{APP_VERSION}이 최신 버전입니다.")
        def failed(msg):
            if hasattr(self, "update_status"):
                self.update_status.setText(msg)
            if show_current:
                QMessageBox.warning(self, "NOVA Update", msg)
        self.run_task(check_latest, done, failed)

    def install_update(self):
        info = self.latest_update
        if not info or not info.available:
            self.show_error("설치할 새 업데이트가 없습니다."); return
        self.install_update_btn.setEnabled(False); self.update_status.setText("업데이트 다운로드 및 검증 중…")
        def done(payload):
            try:
                self._launch_updater(payload)
            except Exception as e:
                self.install_update_btn.setEnabled(True); self.show_error(str(e))
        def failed(msg):
            self.install_update_btn.setEnabled(True); self.update_status.setText(msg); self.show_error(msg)
        self.run_task(lambda: stage_update(info), done, failed)

    def _launch_updater(self, payload):
        import os, shutil, subprocess, sys
        from pathlib import Path

        payload = Path(payload).resolve()
        frozen = bool(getattr(sys, "frozen", False))
        if frozen:
            target = Path(sys.executable).resolve().parent
            bundled = target / "NOVAUpdater.exe"
            if not bundled.exists():
                raise RuntimeError("NOVAUpdater.exe가 없어 자동 업데이트를 시작할 수 없습니다.")
            updater = UPDATE_DIR / "NOVAUpdater.exe"
            shutil.copy2(bundled, updater)
            cmd = [str(updater), "--pid", str(os.getpid()), "--source", str(payload), "--target", str(target),
                   "--restart-exe", str(target / "NOVA.exe")]
        else:
            target = Path(__file__).resolve().parent.parent
            updater_script = target / "nova_updater.py"
            cmd = [sys.executable, str(updater_script), "--pid", str(os.getpid()), "--source", str(payload), "--target", str(target),
                   "--restart-exe", sys.executable, "--restart-arg", str(target / "main.py"),
                   "--requirements", str(target / "requirements.txt")]
        subprocess.Popen(cmd, cwd=target)
        self.update_status.setText("NOVA를 종료하고 업데이트를 적용합니다…")
        QApplication.quit()

    def set_kill_switch(self, checked: bool):
        self.db.set_setting("kill_switch", "1" if checked else "0")
        self.db.log("Kill Switch enabled" if checked else "Kill Switch disabled", "WARN")
        self.refresh_safety()

    def save_safety(self):
        self.db.set_setting("max_order_value", self.max_order.value())
        self.db.set_setting("max_position_pct", self.max_pos.value())
        self.db.set_setting("cooldown_seconds", self.cooldown.value())
        self.db.log("Safety limits updated")
        self.statusBar().showMessage("Safety limits saved")

    def reset_account(self):
        ans = QMessageBox.question(self, "Reset paper account", "모의계좌, 주문, 규칙을 전부 초기화할까요?")
        if ans == QMessageBox.StandardButton.Yes:
            self.db.reset_paper_account(); self.current_quote = None; self.refresh_all(); self.statusBar().showMessage("Paper account reset")


def launch():
    app = QApplication.instance() or QApplication([])
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    w = MainWindow(); w.show()
    return app.exec()
