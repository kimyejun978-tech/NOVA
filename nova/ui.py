from __future__ import annotations

from functools import partial
from typing import Any, Callable

import pandas as pd
from PySide6.QtCore import QMargins, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QAction, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
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
    QProgressBar,
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

from .advisor import Advisor
from .analysis_engine import AnalysisEngine, AnalysisResult
from .broker import PaperBroker
from .config import APP_NAME, APP_VERSION, AUTO_SCAN_SECONDS, UPDATE_DIR
from .db import Database
from .market import YahooMarketData, normalize_ticker
from .updater import UpdateInfo, check_latest, stage_update
from .rules import RuleEngine
from .safety import SafetyEngine


STYLE = """
QMainWindow, QWidget {
    background: #090c11;
    color: #edf2f8;
    font-family: "Segoe UI", "Malgun Gothic";
    font-size: 13px;
}
QMenuBar {
    background: #090c11;
    color: #98a5b6;
    border-bottom: 1px solid #161d27;
    padding: 2px 6px;
}
QMenuBar::item:selected { background: #151c26; color: #f4f7fb; border-radius: 5px; }
QMenu { background: #111720; color: #e7ecf3; border: 1px solid #27313e; }
QMenu::item:selected { background: #1c2735; }

QFrame#Sidebar {
    background: #0c1016;
    border-right: 1px solid #1b2330;
}
QFrame#TopBar {
    background: transparent;
    border-bottom: 1px solid #171e28;
}
QFrame#Card {
    background: #10161f;
    border: 1px solid #202a37;
    border-radius: 14px;
}
QFrame#HeroCard {
    background: #111a26;
    border: 1px solid #263346;
    border-radius: 16px;
}
QFrame#MetricCard {
    background: #0f151d;
    border: 1px solid #202a37;
    border-radius: 13px;
}
QFrame#DangerCard {
    background: #171217;
    border: 1px solid #40242c;
    border-radius: 14px;
}

QLabel#Brand {
    font-size: 25px;
    font-weight: 800;
    letter-spacing: 3px;
    color: #f5f8fc;
}
QLabel#BrandSub {
    color: #5d6c80;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
}
QLabel#PageTitle {
    font-size: 22px;
    font-weight: 750;
    color: #f4f7fb;
}
QLabel#Hero {
    font-size: 29px;
    font-weight: 800;
    color: #f5f8fc;
}
QLabel#HeroSub {
    color: #8997aa;
    font-size: 13px;
}
QLabel#Muted { color: #7f8da0; }
QLabel#Tiny {
    color: #667588;
    font-size: 11px;
}
QLabel#Section {
    font-size: 15px;
    font-weight: 700;
    color: #e8edf4;
}
QLabel#MetricTitle {
    color: #7d8b9d;
    font-size: 11px;
    font-weight: 700;
}
QLabel#Metric {
    font-size: 23px;
    font-weight: 750;
    color: #f4f7fb;
}
QLabel#MetricSmall {
    color: #7e8b9c;
    font-size: 11px;
}
QLabel#Badge {
    background: #162130;
    color: #8eb6ff;
    border: 1px solid #263c5b;
    border-radius: 9px;
    padding: 4px 8px;
    font-size: 10px;
    font-weight: 700;
}
QLabel#BadgeGood {
    background: #10251d;
    color: #62d99f;
    border: 1px solid #214a39;
    border-radius: 9px;
    padding: 4px 8px;
    font-size: 10px;
    font-weight: 700;
}
QLabel#BadgeDanger {
    background: #2b151b;
    color: #ff8b97;
    border: 1px solid #5a2933;
    border-radius: 9px;
    padding: 4px 8px;
    font-size: 10px;
    font-weight: 700;
}

QPushButton {
    background: #151d28;
    border: 1px solid #293647;
    border-radius: 9px;
    padding: 9px 13px;
    color: #e7edf5;
    font-weight: 600;
}
QPushButton:hover { background: #1c2735; border-color: #35465b; }
QPushButton:pressed { background: #101720; }
QPushButton:disabled { color: #536071; background: #11161d; border-color: #1c2430; }

QPushButton#Primary {
    background: #4f7cff;
    border-color: #4f7cff;
    color: #ffffff;
    font-weight: 700;
}
QPushButton#Primary:hover { background: #628aff; border-color: #628aff; }

QPushButton#Buy {
    background: #153527;
    border-color: #275a43;
    color: #78dfa9;
    font-weight: 750;
}
QPushButton#Buy:hover { background: #1b4332; }

QPushButton#Sell {
    background: #321a21;
    border-color: #62313d;
    color: #ff919d;
    font-weight: 750;
}
QPushButton#Sell:hover { background: #43212b; }

QPushButton#Danger {
    background: #2b151b;
    border-color: #5b2a35;
    color: #ff8b97;
    font-weight: 750;
    padding: 12px 14px;
}
QPushButton#Danger:hover { background: #3a1b24; }
QPushButton#Danger:checked {
    background: #a83243;
    border-color: #d74b5f;
    color: white;
}

QPushButton#Nav {
    text-align: left;
    border: none;
    background: transparent;
    color: #7d8a9d;
    padding: 11px 13px;
    border-radius: 9px;
    font-weight: 650;
}
QPushButton#Nav:hover {
    background: #121923;
    color: #cbd4df;
}
QPushButton#Nav:checked {
    background: #172232;
    color: #eef4ff;
    border: 1px solid #23344c;
}

QPushButton#Segment {
    background: #10161f;
    border: 1px solid #273241;
    color: #7f8da0;
    padding: 7px 12px;
}
QPushButton#Segment:checked {
    background: #1c2b40;
    border-color: #35547d;
    color: #b9d0ff;
}

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit {
    background: #0c1118;
    border: 1px solid #263141;
    border-radius: 9px;
    padding: 8px 10px;
    color: #edf2f8;
    selection-background-color: #345ea8;
}
QLineEdit {
    min-height: 20px;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QTextEdit:focus {
    border-color: #4f7cff;
}
QComboBox::drop-down { border: none; width: 24px; }

QProgressBar {
    background: #0b1016;
    border: 1px solid #1f2936;
    border-radius: 5px;
    height: 8px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background: #4f7cff;
    border-radius: 4px;
}
QProgressBar#ConfidenceBar::chunk { background: #56b98c; }

QTableWidget {
    background: #0d1219;
    alternate-background-color: #101720;
    border: 1px solid #202a37;
    border-radius: 10px;
    gridline-color: transparent;
    outline: none;
}
QHeaderView::section {
    background: #121923;
    color: #78879a;
    border: none;
    border-bottom: 1px solid #26303c;
    padding: 9px;
    font-size: 11px;
    font-weight: 700;
}
QTableWidget::item {
    padding: 7px;
    border-bottom: 1px solid #151d27;
}
QTableWidget::item:selected {
    background: #1c2d45;
    color: #f3f7fc;
}

QStatusBar {
    background: #0b0f14;
    color: #68778a;
    border-top: 1px solid #161d27;
}
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


def card(object_name: str = "Card") -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName(object_name)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(17, 15, 17, 15)
    layout.setSpacing(8)
    return frame, layout


def section_title(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("Section")
    return label


def muted(text: str, wrap: bool = False) -> QLabel:
    label = QLabel(text)
    label.setObjectName("Muted")
    label.setWordWrap(wrap)
    return label


def item(text: Any) -> QTableWidgetItem:
    x = QTableWidgetItem(str(text))
    x.setFlags(x.flags() & ~Qt.ItemFlag.ItemIsEditable)
    return x


def metric_card(title: str, subtitle: str = "") -> tuple[QFrame, QLabel]:
    frame, lay = card("MetricCard")
    t = QLabel(title.upper())
    t.setObjectName("MetricTitle")
    value = QLabel("-")
    value.setObjectName("Metric")
    lay.addWidget(t)
    lay.addWidget(value)
    if subtitle:
        hint = QLabel(subtitle)
        hint.setObjectName("MetricSmall")
        lay.addWidget(hint)
    else:
        lay.addStretch(1)
    return frame, value


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

        self.page_meta = [
            ("Overview", "Paper portfolio and recent activity"),
            ("Analyze", "ML prediction and explainable analysis"),
            ("Paper Trade", "Manual simulation order ticket"),
            ("Rules", "User-controlled one-shot automation"),
            ("Safety", "Hard limits independent from AI"),
            ("Updates", "NOVA release and updater status"),
        ]

        self.setWindowTitle(f"{APP_NAME} — Paper Trading v{APP_VERSION}")
        self.resize(1360, 860)
        self.setMinimumSize(1080, 720)
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
        refresh = QAction("Refresh", self)
        refresh.triggered.connect(self.refresh_all)
        menu.addAction(refresh)
        check_update = QAction("Check updates", self)
        check_update.triggered.connect(lambda: self.check_updates_silent(show_current=True))
        menu.addAction(check_update)

    def _build_ui(self):
        root = QWidget()
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(218)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(16, 22, 16, 16)
        side.setSpacing(5)

        brand = QLabel("NOVA")
        brand.setObjectName("Brand")
        sub = QLabel("PAPER INTELLIGENCE")
        sub.setObjectName("BrandSub")
        side.addWidget(brand)
        side.addWidget(sub)
        side.addSpacing(22)

        nav_caption = QLabel("WORKSPACE")
        nav_caption.setObjectName("Tiny")
        side.addWidget(nav_caption)
        side.addSpacing(4)

        self.nav_buttons = []
        pages = [
            self._make_dashboard(),
            self._make_analysis(),
            self._make_trade(),
            self._make_rules(),
            self._make_safety(),
            self._make_updates(),
        ]
        nav_names = ["Overview", "Analyze", "Paper Trade", "Rules", "Safety", "Updates"]

        self.stack = QStackedWidget()
        for idx, (name, page) in enumerate(zip(nav_names, pages)):
            b = QPushButton(name)
            b.setObjectName("Nav")
            b.setCheckable(True)
            b.clicked.connect(partial(self._switch_page, idx))
            self.nav_buttons.append(b)
            side.addWidget(b)
            self.stack.addWidget(page)
        self.nav_buttons[0].setChecked(True)

        side.addStretch(1)

        mode_card, mode_l = card("Card")
        mode_l.setContentsMargins(12, 11, 12, 11)
        sim = QLabel("PAPER MODE")
        sim.setObjectName("Badge")
        mode_l.addWidget(sim, alignment=Qt.AlignmentFlag.AlignLeft)
        self.kill_badge = QLabel("Safety: checking...")
        self.kill_badge.setObjectName("Tiny")
        mode_l.addWidget(self.kill_badge)
        version = QLabel(f"v{APP_VERSION} · no live broker")
        version.setObjectName("Tiny")
        mode_l.addWidget(version)
        side.addWidget(mode_card)

        content = QWidget()
        content_l = QVBoxLayout(content)
        content_l.setContentsMargins(24, 0, 24, 18)
        content_l.setSpacing(0)

        topbar = QFrame()
        topbar.setObjectName("TopBar")
        topbar.setFixedHeight(74)
        top = QHBoxLayout(topbar)
        top.setContentsMargins(0, 12, 0, 12)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.page_title_label = QLabel(self.page_meta[0][0])
        self.page_title_label.setObjectName("PageTitle")
        self.page_subtitle_label = QLabel(self.page_meta[0][1])
        self.page_subtitle_label.setObjectName("Tiny")
        title_box.addWidget(self.page_title_label)
        title_box.addWidget(self.page_subtitle_label)
        top.addLayout(title_box)
        top.addStretch(1)

        self.top_safety_badge = QLabel("SAFETY")
        self.top_safety_badge.setObjectName("BadgeGood")
        top.addWidget(self.top_safety_badge)

        paper_badge = QLabel("SIMULATION")
        paper_badge.setObjectName("Badge")
        top.addWidget(paper_badge)

        content_l.addWidget(topbar)
        content_l.addSpacing(18)
        content_l.addWidget(self.stack, 1)

        outer.addWidget(sidebar)
        outer.addWidget(content, 1)
        self.setCentralWidget(root)
        self.statusBar().showMessage("NOVA ready · simulation only")

    def _switch_page(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, b in enumerate(self.nav_buttons):
            b.setChecked(i == index)
        title, subtitle = self.page_meta[index]
        self.page_title_label.setText(title)
        self.page_subtitle_label.setText(subtitle)
        if index in (0, 2, 3, 4):
            self.refresh_all()

    def _make_dashboard(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(14)

        hero, hl = card("HeroCard")
        hero_top = QHBoxLayout()
        hero_text = QVBoxLayout()
        hero_text.setSpacing(4)
        title = QLabel("Paper portfolio")
        title.setObjectName("Hero")
        desc = QLabel("실계좌와 완전히 분리된 모의 자동매매 환경")
        desc.setObjectName("HeroSub")
        hero_text.addWidget(title)
        hero_text.addWidget(desc)
        hero_top.addLayout(hero_text)
        hero_top.addStretch(1)

        analyze_shortcut = QPushButton("Analyze stock")
        analyze_shortcut.setObjectName("Primary")
        analyze_shortcut.clicked.connect(lambda: self._switch_page(1))
        trade_shortcut = QPushButton("New paper order")
        trade_shortcut.clicked.connect(lambda: self._switch_page(2))
        hero_top.addWidget(analyze_shortcut)
        hero_top.addWidget(trade_shortcut)
        hl.addLayout(hero_top)

        note = QLabel("Market data can be delayed. NOVA v1 never sends live brokerage orders.")
        note.setObjectName("Tiny")
        hl.addWidget(note)
        lay.addWidget(hero)

        metrics = QHBoxLayout()
        metrics.setSpacing(12)
        self.equity_card, self.asset_value = metric_card("Paper equity", "cash + position book value")
        self.cash_card, self.cash_value = metric_card("Cash", "available simulation balance")
        self.invested_card, self.invested_value = metric_card("Invested", "position book value")
        self.pos_card, self.pos_value = metric_card("Positions", "open simulated holdings")
        metrics.addWidget(self.equity_card)
        metrics.addWidget(self.cash_card)
        metrics.addWidget(self.invested_card)
        metrics.addWidget(self.pos_card)
        lay.addLayout(metrics)

        tables = QHBoxLayout()
        tables.setSpacing(12)

        pos_card, pl = card()
        pl.addWidget(section_title("Open positions"))
        self.positions_table = QTableWidget(0, 5)
        self.positions_table.setHorizontalHeaderLabels(["Ticker", "Qty", "Avg", "Book value", "Updated"])
        self._setup_table(self.positions_table)
        pl.addWidget(self.positions_table)
        tables.addWidget(pos_card, 5)

        orders_card, ol = card()
        ol.addWidget(section_title("Recent activity"))
        self.orders_table = QTableWidget(0, 7)
        self.orders_table.setHorizontalHeaderLabels(["Time", "Ticker", "Side", "Qty", "Price", "Source", "Status"])
        self._setup_table(self.orders_table)
        ol.addWidget(self.orders_table)
        tables.addWidget(orders_card, 6)

        lay.addLayout(tables, 1)
        return page

    def _make_analysis(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        search_card, sl = card("HeroCard")
        search_top = QHBoxLayout()
        search_info = QVBoxLayout()
        search_info.setSpacing(3)
        title = QLabel("Stock intelligence")
        title.setObjectName("Hero")
        subtitle = QLabel("Global Model + stock-specific Model + Data Guard")
        subtitle.setObjectName("HeroSub")
        search_info.addWidget(title)
        search_info.addWidget(subtitle)
        search_top.addLayout(search_info)
        search_top.addStretch(1)

        self.easy_btn = QPushButton("Easy")
        self.detail_btn = QPushButton("Detailed")
        self.easy_btn.setObjectName("Segment")
        self.detail_btn.setObjectName("Segment")
        self.easy_btn.setCheckable(True)
        self.detail_btn.setCheckable(True)
        self.easy_btn.setChecked(True)
        self.easy_btn.clicked.connect(lambda: self.set_analysis_view(True))
        self.detail_btn.clicked.connect(lambda: self.set_analysis_view(False))
        search_top.addWidget(self.easy_btn)
        search_top.addWidget(self.detail_btn)
        sl.addLayout(search_top)

        search_row = QHBoxLayout()
        self.analysis_ticker = QLineEdit()
        self.analysis_ticker.setPlaceholderText("Search ticker or name · 005930.KS / SK하이닉스 / AAPL")
        self.analysis_ticker.returnPressed.connect(self.run_analysis)
        search_row.addWidget(self.analysis_ticker, 5)
        self.horizon = QComboBox()
        self.horizon.addItem("1 day", 1)
        self.horizon.addItem("1 week", 5)
        self.horizon.addItem("1 month", 20)
        self.horizon.setCurrentIndex(1)
        search_row.addWidget(self.horizon, 1)
        self.analyze_btn = QPushButton("Run analysis")
        self.analyze_btn.setObjectName("Primary")
        self.analyze_btn.clicked.connect(self.run_analysis)
        search_row.addWidget(self.analyze_btn)
        sl.addLayout(search_row)
        lay.addWidget(search_card)

        metric_row = QHBoxLayout()
        metric_row.setSpacing(12)

        c1, l1 = card("MetricCard")
        t1 = QLabel("UP PROBABILITY"); t1.setObjectName("MetricTitle"); l1.addWidget(t1)
        self.up_label = QLabel("-")
        self.up_label.setObjectName("Metric")
        self.up_progress = QProgressBar()
        self.up_progress.setRange(0, 100)
        self.up_progress.setTextVisible(False)
        l1.addWidget(self.up_label)
        l1.addWidget(self.up_progress)
        metric_row.addWidget(c1)

        c2, l2 = card("MetricCard")
        t2 = QLabel("REFERENCE RANGE"); t2.setObjectName("MetricTitle"); l2.addWidget(t2)
        self.range_label = QLabel("-")
        self.range_label.setObjectName("Metric")
        range_hint = QLabel("model-estimated interval")
        range_hint.setObjectName("MetricSmall")
        l2.addWidget(self.range_label)
        l2.addWidget(range_hint)
        metric_row.addWidget(c2)

        c3, l3 = card("MetricCard")
        t3 = QLabel("CONFIDENCE"); t3.setObjectName("MetricTitle"); l3.addWidget(t3)
        self.conf_label = QLabel("-")
        self.conf_label.setObjectName("Metric")
        self.conf_progress = QProgressBar()
        self.conf_progress.setObjectName("ConfidenceBar")
        self.conf_progress.setRange(0, 100)
        self.conf_progress.setTextVisible(False)
        l3.addWidget(self.conf_label)
        l3.addWidget(self.conf_progress)
        metric_row.addWidget(c3)

        c4, l4 = card("MetricCard")
        t4 = QLabel("DATA TIER"); t4.setObjectName("MetricTitle"); l4.addWidget(t4)
        self.tier_label = QLabel("-")
        self.tier_label.setObjectName("Metric")
        tier_hint = QLabel("Data Guard availability")
        tier_hint.setObjectName("MetricSmall")
        l4.addWidget(self.tier_label)
        l4.addWidget(tier_hint)
        metric_row.addWidget(c4)
        lay.addLayout(metric_row)

        bottom = QHBoxLayout()
        bottom.setSpacing(12)

        left_card, left_l = card()
        advisory_head = QHBoxLayout()
        advisory_head.addWidget(section_title("NOVA advisory"))
        advisory_head.addStretch(1)
        advisory_badge = QLabel("ADVISORY ONLY")
        advisory_badge.setObjectName("Badge")
        advisory_head.addWidget(advisory_badge)
        left_l.addLayout(advisory_head)

        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setMinimumHeight(210)
        self.analysis_text.setPlaceholderText("Run an analysis to see NOVA's explanation.")
        left_l.addWidget(self.analysis_text)

        advice_sep = QFrame()
        advice_sep.setFixedHeight(1)
        advice_sep.setStyleSheet("background:#202a37;border:none;")
        left_l.addWidget(advice_sep)
        rule_title = QLabel("Strategy note")
        rule_title.setObjectName("MetricTitle")
        left_l.addWidget(rule_title)
        self.rule_advice = QLabel("분석 후 전략 권고가 표시됩니다.")
        self.rule_advice.setWordWrap(True)
        self.rule_advice.setObjectName("Muted")
        left_l.addWidget(self.rule_advice)
        bottom.addWidget(left_card, 4)

        self.chart_card, chart_l = card()
        chart_head = QHBoxLayout()
        chart_head.addWidget(section_title("Price context"))
        chart_head.addStretch(1)
        chart_badge = QLabel("CLOSE + SMA20")
        chart_badge.setObjectName("Badge")
        chart_head.addWidget(chart_badge)
        chart_l.addLayout(chart_head)
        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.chart_view.setMinimumHeight(300)
        chart_l.addWidget(self.chart_view)
        bottom.addWidget(self.chart_card, 6)

        lay.addLayout(bottom, 1)
        self.chart_card.setVisible(False)
        return page

    def _make_trade(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        top = QHBoxLayout()
        top.setSpacing(12)

        ticket, tl = card("HeroCard")
        ticket_head = QHBoxLayout()
        ticket_head.addWidget(section_title("Order ticket"))
        ticket_head.addStretch(1)
        badge = QLabel("PAPER ONLY")
        badge.setObjectName("Badge")
        ticket_head.addWidget(badge)
        tl.addLayout(ticket_head)

        self.trade_ticker = QLineEdit()
        self.trade_ticker.setPlaceholderText("Ticker · 005930.KS / AAPL")
        self.quote_btn = QPushButton("Load price")
        self.quote_btn.clicked.connect(self.fetch_trade_quote)
        quote_row = QHBoxLayout()
        quote_row.addWidget(self.trade_ticker, 1)
        quote_row.addWidget(self.quote_btn)
        tl.addLayout(quote_row)

        price_title = QLabel("LAST PRICE")
        price_title.setObjectName("MetricTitle")
        tl.addWidget(price_title)
        self.trade_price = QLabel("No quote loaded")
        self.trade_price.setObjectName("Metric")
        tl.addWidget(self.trade_price)

        qty_label = QLabel("Quantity")
        qty_label.setObjectName("MetricTitle")
        tl.addWidget(qty_label)
        self.trade_qty = QSpinBox()
        self.trade_qty.setRange(1, 1_000_000)
        self.trade_qty.setValue(1)
        tl.addWidget(self.trade_qty)

        trade_buttons = QHBoxLayout()
        self.buy_btn = QPushButton("BUY · PAPER")
        self.buy_btn.setObjectName("Buy")
        self.buy_btn.clicked.connect(lambda: self.place_manual("BUY"))
        self.sell_btn = QPushButton("SELL · PAPER")
        self.sell_btn.setObjectName("Sell")
        self.sell_btn.clicked.connect(lambda: self.place_manual("SELL"))
        trade_buttons.addWidget(self.buy_btn)
        trade_buttons.addWidget(self.sell_btn)
        tl.addLayout(trade_buttons)
        top.addWidget(ticket, 4)

        info, il = card()
        il.addWidget(section_title("Execution rules"))
        il.addWidget(muted("NOVA never routes this ticket to a real broker.", True))
        il.addSpacing(6)

        rows = [
            ("Price", "Uses the last loaded market quote"),
            ("Safety", "Order value, position weight and cooldown are checked"),
            ("AI", "Can explain or suggest, but cannot submit or edit orders"),
            ("Persistence", "Paper fills are saved locally in NOVA's database"),
        ]
        for label_text, body in rows:
            row_title = QLabel(label_text.upper())
            row_title.setObjectName("MetricTitle")
            il.addWidget(row_title)
            il.addWidget(muted(body, True))
            il.addSpacing(5)
        il.addStretch(1)
        top.addWidget(info, 3)

        lay.addLayout(top)

        history, hl = card()
        history_head = QHBoxLayout()
        history_head.addWidget(section_title("Order history"))
        history_head.addStretch(1)
        hist_badge = QLabel("SIMULATED FILLS")
        hist_badge.setObjectName("Badge")
        history_head.addWidget(hist_badge)
        hl.addLayout(history_head)

        self.trade_orders = QTableWidget(0, 8)
        self.trade_orders.setHorizontalHeaderLabels(["Time", "Ticker", "Side", "Qty", "Price", "Total", "Source", "Status"])
        self._setup_table(self.trade_orders)
        hl.addWidget(self.trade_orders)
        lay.addWidget(history, 1)
        return page

    def _make_rules(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        top = QHBoxLayout()
        top.setSpacing(12)

        builder, bl = card("HeroCard")
        builder_head = QHBoxLayout()
        builder_head.addWidget(section_title("Rule builder"))
        builder_head.addStretch(1)
        badge = QLabel("ONE-SHOT")
        badge.setObjectName("Badge")
        builder_head.addWidget(badge)
        bl.addLayout(builder_head)
        bl.addWidget(muted("조건이 한 번 성공 체결되면 규칙은 자동으로 OFF됩니다.", True))

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        self.rule_ticker = QLineEdit()
        self.rule_ticker.setPlaceholderText("005930.KS")
        self.rule_comp = QComboBox()
        self.rule_comp.addItem("price <=", "<=")
        self.rule_comp.addItem("price >=", ">=")
        self.rule_price = QDoubleSpinBox()
        self.rule_price.setRange(0.01, 1_000_000_000)
        self.rule_price.setDecimals(2)
        self.rule_price.setValue(70000)
        self.rule_side = QComboBox()
        self.rule_side.addItems(["BUY", "SELL"])
        self.rule_qty = QSpinBox()
        self.rule_qty.setRange(1, 1_000_000)
        self.rule_qty.setValue(1)

        grid.addWidget(QLabel("Ticker"), 0, 0)
        grid.addWidget(self.rule_ticker, 0, 1)
        grid.addWidget(QLabel("Condition"), 0, 2)
        grid.addWidget(self.rule_comp, 0, 3)
        grid.addWidget(QLabel("Trigger"), 1, 0)
        grid.addWidget(self.rule_price, 1, 1)
        grid.addWidget(QLabel("Action"), 1, 2)
        grid.addWidget(self.rule_side, 1, 3)
        grid.addWidget(QLabel("Quantity"), 2, 0)
        grid.addWidget(self.rule_qty, 2, 1)
        bl.addLayout(grid)

        builder_actions = QHBoxLayout()
        add = QPushButton("Create rule")
        add.setObjectName("Primary")
        add.clicked.connect(self.add_rule)
        scan = QPushButton("Scan now")
        scan.clicked.connect(self.scan_rules_async)
        builder_actions.addWidget(add)
        builder_actions.addWidget(scan)
        builder_actions.addStretch(1)
        bl.addLayout(builder_actions)
        top.addWidget(builder, 5)

        policy, pl = card()
        pl.addWidget(section_title("Permission boundary"))
        ai_badge = QLabel("AI CANNOT EDIT RULES")
        ai_badge.setObjectName("BadgeGood")
        pl.addWidget(ai_badge, alignment=Qt.AlignmentFlag.AlignLeft)
        pl.addWidget(muted("Only rules created or changed by you can become executable.", True))
        pl.addWidget(muted("AI recommendations stay advisory and never write into this rule table.", True))
        pl.addStretch(1)
        top.addWidget(policy, 3)
        lay.addLayout(top)

        list_card, ll = card()
        list_head = QHBoxLayout()
        list_head.addWidget(section_title("Active automation"))
        list_head.addStretch(1)
        self.rule_status = QLabel(f"Auto scan · every {AUTO_SCAN_SECONDS}s")
        self.rule_status.setObjectName("Tiny")
        list_head.addWidget(self.rule_status)
        ll.addLayout(list_head)

        self.rules_table = QTableWidget(0, 8)
        self.rules_table.setHorizontalHeaderLabels(["ID", "Ticker", "Condition", "Price", "Side", "Qty", "Enabled", "Last trigger"])
        self._setup_table(self.rules_table)
        self.rules_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        ll.addWidget(self.rules_table)

        actions = QHBoxLayout()
        toggle = QPushButton("Enable / Disable")
        toggle.clicked.connect(self.toggle_selected_rule)
        delete = QPushButton("Delete selected")
        delete.setObjectName("Sell")
        delete.clicked.connect(self.delete_selected_rule)
        actions.addWidget(toggle)
        actions.addWidget(delete)
        actions.addStretch(1)
        ll.addLayout(actions)
        lay.addWidget(list_card, 1)
        return page

    def _make_safety(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        kill_card, kl = card("DangerCard")
        kill_head = QHBoxLayout()
        kill_text = QVBoxLayout()
        kill_text.setSpacing(3)
        kt = QLabel("Emergency trading lock")
        kt.setObjectName("Hero")
        kd = QLabel("Hard safety switch independent from ML and AI")
        kd.setObjectName("HeroSub")
        kill_text.addWidget(kt)
        kill_text.addWidget(kd)
        kill_head.addLayout(kill_text)
        kill_head.addStretch(1)
        self.kill_switch = QPushButton("KILL SWITCH OFF")
        self.kill_switch.setObjectName("Danger")
        self.kill_switch.setCheckable(True)
        self.kill_switch.clicked.connect(self.set_kill_switch)
        kill_head.addWidget(self.kill_switch)
        kl.addLayout(kill_head)
        kl.addWidget(muted("When enabled, every new simulated BUY/SELL is blocked. Existing positions are kept.", True))
        lay.addWidget(kill_card)

        mid = QHBoxLayout()
        mid.setSpacing(12)

        lim_card, ll = card()
        ll.addWidget(section_title("Risk limits"))
        grid = QGridLayout()
        grid.setVerticalSpacing(11)
        self.max_order = QDoubleSpinBox()
        self.max_order.setRange(1_000, 1_000_000_000)
        self.max_order.setDecimals(0)
        self.max_order.setSuffix(" KRW")
        self.max_pos = QDoubleSpinBox()
        self.max_pos.setRange(1, 100)
        self.max_pos.setDecimals(1)
        self.max_pos.setSuffix(" %")
        self.cooldown = QSpinBox()
        self.cooldown.setRange(0, 86_400)
        self.cooldown.setSuffix(" sec")
        grid.addWidget(QLabel("Max order value"), 0, 0)
        grid.addWidget(self.max_order, 0, 1)
        grid.addWidget(QLabel("Max position weight"), 1, 0)
        grid.addWidget(self.max_pos, 1, 1)
        grid.addWidget(QLabel("Same ticker cooldown"), 2, 0)
        grid.addWidget(self.cooldown, 2, 1)
        ll.addLayout(grid)
        save = QPushButton("Save safety limits")
        save.setObjectName("Primary")
        save.clicked.connect(self.save_safety)
        ll.addWidget(save, alignment=Qt.AlignmentFlag.AlignRight)
        mid.addWidget(lim_card, 5)

        architecture, al = card()
        al.addWidget(section_title("Safety architecture"))
        safe_badge = QLabel("HARD-CODED GATE")
        safe_badge.setObjectName("BadgeGood")
        al.addWidget(safe_badge, alignment=Qt.AlignmentFlag.AlignLeft)
        al.addWidget(muted("Manual order → Safety Engine → Paper Broker", True))
        al.addWidget(muted("Rule trigger → Safety Engine → Paper Broker", True))
        al.addWidget(muted("AI advisory has no broker or rule mutation permission.", True))
        al.addStretch(1)
        mid.addWidget(architecture, 4)
        lay.addLayout(mid)

        reset_card, rl = card()
        reset_head = QHBoxLayout()
        reset_text = QVBoxLayout()
        reset_text.addWidget(section_title("Reset simulation"))
        reset_text.addWidget(muted("모의잔고·포지션·주문·규칙을 모두 지우고 10,000,000 KRW로 초기화합니다.", True))
        reset_head.addLayout(reset_text)
        reset_head.addStretch(1)
        reset = QPushButton("Reset paper account")
        reset.setObjectName("Sell")
        reset.clicked.connect(self.reset_account)
        reset_head.addWidget(reset)
        rl.addLayout(reset_head)
        lay.addWidget(reset_card)
        lay.addStretch(1)
        return page

    def _make_updates(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        hero, hl = card("HeroCard")
        top = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("NOVA Update")
        title.setObjectName("Hero")
        desc = QLabel("GitHub Release 기반 자동 업데이트")
        desc.setObjectName("HeroSub")
        title_box.addWidget(title)
        title_box.addWidget(desc)
        top.addLayout(title_box)
        top.addStretch(1)
        current_badge = QLabel(f"CURRENT · {APP_VERSION}")
        current_badge.setObjectName("Badge")
        top.addWidget(current_badge)
        hl.addLayout(top)
        hl.addWidget(muted("Update packages are SHA-256 verified before the standalone updater replaces NOVA. Local paper-trading data is preserved.", True))
        lay.addWidget(hero)

        c, cl = card()
        status_head = QHBoxLayout()
        status_head.addWidget(section_title("Release status"))
        status_head.addStretch(1)
        self.update_current = QLabel(f"Current version: {APP_VERSION}")
        self.update_current.setObjectName("Tiny")
        status_head.addWidget(self.update_current)
        cl.addLayout(status_head)

        self.update_status = QLabel("아직 업데이트를 확인하지 않았습니다.")
        self.update_status.setWordWrap(True)
        self.update_status.setObjectName("Muted")
        cl.addWidget(self.update_status)

        notes_label = QLabel("RELEASE NOTES")
        notes_label.setObjectName("MetricTitle")
        cl.addWidget(notes_label)
        self.update_notes = QTextEdit()
        self.update_notes.setReadOnly(True)
        self.update_notes.setMinimumHeight(210)
        cl.addWidget(self.update_notes)

        row = QHBoxLayout()
        check = QPushButton("Check for updates")
        check.clicked.connect(lambda: self.check_updates_silent(show_current=True))
        self.install_update_btn = QPushButton("Update & restart")
        self.install_update_btn.setObjectName("Primary")
        self.install_update_btn.setEnabled(False)
        self.install_update_btn.clicked.connect(self.install_update)
        row.addWidget(check)
        row.addWidget(self.install_update_btn)
        row.addStretch(1)
        cl.addLayout(row)

        lay.addWidget(c, 1)
        return page

    def _setup_table(self, table: QTableWidget):
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(38)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setAlternatingRowColors(True)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setShowGrid(False)

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
        invested = sum(int(p["qty"]) * float(p["avg_price"]) for p in positions)
        book = cash + invested

        self.cash_value.setText(f"₩{cash:,.0f}")
        self.asset_value.setText(f"₩{book:,.0f}")
        self.invested_value.setText(f"₩{invested:,.0f}")
        self.pos_value.setText(str(len(positions)))

        self.positions_table.setRowCount(len(positions))
        for r, p in enumerate(positions):
            vals = [p["ticker"], p["qty"], f"{p['avg_price']:,.2f}", f"{p['qty'] * p['avg_price']:,.0f}", p["updated_at"]]
            for c, v in enumerate(vals):
                self.positions_table.setItem(r, c, item(v))

        orders = self.db.recent_orders(12)
        self.orders_table.setRowCount(len(orders))
        for r, o in enumerate(orders):
            vals = [o["created_at"], o["ticker"], o["side"], o["qty"], f"{o['price']:,.2f}", o["source"], o["status"]]
            for c, v in enumerate(vals):
                self.orders_table.setItem(r, c, item(v))

    def refresh_orders(self):
        if not hasattr(self, "trade_orders"):
            return
        orders = self.db.recent_orders(80)
        self.trade_orders.setRowCount(len(orders))
        for r, o in enumerate(orders):
            vals = [o["created_at"], o["ticker"], o["side"], o["qty"], f"{o['price']:,.2f}", f"{o['total']:,.0f}", o["source"], o["status"]]
            for c, v in enumerate(vals):
                self.trade_orders.setItem(r, c, item(v))

    def refresh_rules(self):
        if not hasattr(self, "rules_table"):
            return
        rules = self.db.rules()
        self.rules_table.setRowCount(len(rules))
        for r, x in enumerate(rules):
            vals = [x["id"], x["ticker"], x["comparator"], f"{x['trigger_price']:,.2f}", x["side"], x["qty"], "ON" if x["enabled"] else "OFF", x["last_trigger_at"] or "-"]
            for c, v in enumerate(vals):
                self.rules_table.setItem(r, c, item(v))

    def refresh_safety(self):
        if not hasattr(self, "kill_switch"):
            return
        on = self.db.get_setting("kill_switch", "0") == "1"
        self.kill_switch.blockSignals(True)
        self.kill_switch.setChecked(on)
        self.kill_switch.blockSignals(False)
        self.kill_switch.setText("KILL SWITCH ON" if on else "KILL SWITCH OFF")
        self.kill_badge.setText("Safety: locked" if on else "Safety: armed")
        self.top_safety_badge.setText("SAFETY LOCKED" if on else "SAFETY ARMED")
        self.top_safety_badge.setObjectName("BadgeDanger" if on else "BadgeGood")
        self.top_safety_badge.style().unpolish(self.top_safety_badge)
        self.top_safety_badge.style().polish(self.top_safety_badge)
        self.max_order.setValue(float(self.db.get_setting("max_order_value", 2_000_000)))
        self.max_pos.setValue(float(self.db.get_setting("max_position_pct", 25)))
        self.cooldown.setValue(int(float(self.db.get_setting("cooldown_seconds", 60))))

    def run_analysis(self):
        raw = self.analysis_ticker.text().strip()
        if not raw:
            self.show_error("분석할 종목을 입력하세요.")
            return
        try:
            ticker = normalize_ticker(raw)
        except Exception as e:
            self.show_error(str(e))
            return

        horizon = int(self.horizon.currentData())
        self.analyze_btn.setEnabled(False)
        self.analyze_btn.setText("Analyzing...")
        self.statusBar().showMessage(f"{ticker} · Data Guard → Stock ML → Global ML → Ensemble")

        def task():
            return self.analysis_engine.analyze(ticker, horizon_days=horizon)

        def done(result):
            self.analyze_btn.setEnabled(True)
            self.analyze_btn.setText("Run analysis")
            self.current_analysis = result
            self.render_analysis()
            warnings = sum(1 for x in result.guard.issues if x.severity in ("WARN", "BLOCK"))
            self.statusBar().showMessage(
                f"{result.ticker} complete · market datasets {result.market_dataset_count} · data warnings {warnings}"
            )

        def failed(msg):
            self.analyze_btn.setEnabled(True)
            self.analyze_btn.setText("Run analysis")
            self.show_error(msg)

        self.run_task(task, done, failed)

    def set_analysis_view(self, easy: bool):
        self.analysis_easy = easy
        self.easy_btn.setChecked(easy)
        self.detail_btn.setChecked(not easy)
        self.chart_card.setVisible(not easy)
        self.render_analysis()

    def render_analysis(self):
        if not self.current_analysis:
            return
        result = self.current_analysis
        ticker, p, data = result.ticker, result.prediction, result.data

        up_pct = max(0, min(100, int(round(p.up_probability * 100))))
        conf_pct = max(0, min(100, int(round(p.model_score * 100))))

        self.up_label.setText(f"{p.up_probability * 100:.1f}%")
        self.range_label.setText(f"{p.expected_low_price:,.0f} ~ {p.expected_high_price:,.0f}")
        self.conf_label.setText(f"{p.model_score * 100:.0f}/100")
        self.tier_label.setText(p.data_tier)
        self.up_progress.setValue(up_pct)
        self.conf_progress.setValue(conf_pct)

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

        chart = QChart()
        chart.setBackgroundVisible(False)
        chart.setPlotAreaBackgroundVisible(False)
        chart.setMargins(QMargins(8, 8, 8, 8))
        chart.legend().setVisible(True)
        chart.legend().setLabelColor(QColor("#7f8da0"))

        close_s = QLineSeries()
        close_s.setName("Close")
        close_s.setPen(QPen(QColor("#5b8cff"), 2.2))
        sma_s = QLineSeries()
        sma_s.setName("SMA20")
        sma_s.setPen(QPen(QColor("#55bf91"), 1.8))

        for i, v in enumerate(close):
            close_s.append(i, float(v))
        for i, v in enumerate(sma20):
            if pd.notna(v):
                sma_s.append(i, float(v))

        chart.addSeries(close_s)
        chart.addSeries(sma_s)

        x = QValueAxis()
        x.setRange(0, max(1, len(frame) - 1))
        x.setLabelsColor(QColor("#647386"))
        x.setGridLineColor(QColor("#1c2531"))
        x.setTitleText("recent trading days")
        x.setTitleBrush(QColor("#647386"))

        y = QValueAxis()
        mn = float(close.min()) * 0.98
        mx = float(close.max()) * 1.02
        y.setRange(mn, mx)
        y.setLabelFormat("%.0f")
        y.setLabelsColor(QColor("#647386"))
        y.setGridLineColor(QColor("#1c2531"))

        chart.addAxis(x, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(y, Qt.AlignmentFlag.AlignLeft)
        close_s.attachAxis(x)
        close_s.attachAxis(y)
        sma_s.attachAxis(x)
        sma_s.attachAxis(y)
        self.chart_view.setChart(chart)

    def fetch_trade_quote(self):
        raw = self.trade_ticker.text().strip()
        if not raw:
            self.show_error("종목을 입력하세요.")
            return
        try:
            ticker = normalize_ticker(raw)
        except Exception as e:
            self.show_error(str(e))
            return
        self.quote_btn.setEnabled(False)
        self.trade_price.setText("Loading...")
        self.run_task(lambda: self.market.quote(ticker), self._quote_done, self._quote_failed)

    def _quote_done(self, q):
        self.quote_btn.setEnabled(True)
        self.current_quote = q
        self.trade_ticker.setText(q.ticker)
        self.trade_price.setText(f"{q.price:,.2f}  ·  {q.timestamp}")
        self.statusBar().showMessage(f"{q.ticker} quote loaded")

    def _quote_failed(self, msg):
        self.quote_btn.setEnabled(True)
        self.trade_price.setText("No quote loaded")
        self.show_error(msg)

    def place_manual(self, side: str):
        if not self.current_quote:
            self.show_error("먼저 Load price로 가격을 불러오세요.")
            return
        ticker = normalize_ticker(self.trade_ticker.text())
        if ticker != self.current_quote.ticker:
            self.show_error("종목 입력이 마지막으로 불러온 가격과 다릅니다. 가격을 다시 조회하세요.")
            return
        result = self.broker.place_order(ticker, side, self.trade_qty.value(), self.current_quote.price, "MANUAL")
        if result.ok:
            QMessageBox.information(self, "Paper order", result.message)
        else:
            QMessageBox.warning(self, "Paper order", result.message)
        self.refresh_all()

    def add_rule(self):
        try:
            ticker = normalize_ticker(self.rule_ticker.text())
            rid = self.db.add_rule(
                ticker,
                self.rule_comp.currentData(),
                self.rule_price.value(),
                self.rule_side.currentText(),
                self.rule_qty.value(),
            )
            self.db.log(
                f"Rule#{rid} created: {ticker} {self.rule_comp.currentData()} "
                f"{self.rule_price.value()} -> {self.rule_side.currentText()} {self.rule_qty.value()}주"
            )
            self.refresh_rules()
            self.statusBar().showMessage(f"Rule#{rid} added")
        except Exception as e:
            self.show_error(str(e))

    def selected_rule_id(self):
        row = self.rules_table.currentRow()
        if row < 0:
            return None
        return int(self.rules_table.item(row, 0).text())

    def toggle_selected_rule(self):
        rid = self.selected_rule_id()
        if rid is None:
            self.show_error("규칙을 선택하세요.")
            return
        row = self.rules_table.currentRow()
        enabled = self.rules_table.item(row, 6).text() == "ON"
        self.db.set_rule_enabled(rid, not enabled)
        self.refresh_rules()

    def delete_selected_rule(self):
        rid = self.selected_rule_id()
        if rid is None:
            self.show_error("규칙을 선택하세요.")
            return
        self.db.delete_rule(rid)
        self.refresh_rules()

    def scan_rules_async(self):
        if self.rule_scan_running or not self.db.rules(enabled_only=True):
            return
        self.rule_scan_running = True
        self.rule_status.setText("Auto scan · checking prices...")

        def quote_lookup(ticker: str) -> float:
            return self.market.quote(ticker).price

        def task():
            return self.rules.scan(quote_lookup)

        def done(events):
            self.rule_scan_running = False
            triggered = [e for e in events if e.triggered]
            self.rule_status.setText(
                f"Auto scan · every {AUTO_SCAN_SECONDS}s · last fills {len(triggered)}"
            )
            if events:
                for e in events:
                    self.db.log(f"Rule#{e.rule_id}: {e.message}", "INFO" if e.triggered else "WARN")
            self.refresh_all()

        def failed(msg):
            self.rule_scan_running = False
            self.rule_status.setText(f"Auto scan error · {msg}")

        self.run_task(task, done, failed)

    def check_updates_silent(self, show_current: bool = False):
        if hasattr(self, "update_status"):
            self.update_status.setText("업데이트 확인 중...")

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
                self.statusBar().showMessage(f"NOVA {info.version} update available")
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
            self.show_error("설치할 새 업데이트가 없습니다.")
            return
        self.install_update_btn.setEnabled(False)
        self.update_status.setText("업데이트 다운로드 및 검증 중...")

        def done(payload):
            try:
                self._launch_updater(payload)
            except Exception as e:
                self.install_update_btn.setEnabled(True)
                self.show_error(str(e))

        def failed(msg):
            self.install_update_btn.setEnabled(True)
            self.update_status.setText(msg)
            self.show_error(msg)

        self.run_task(lambda: stage_update(info), done, failed)

    def _launch_updater(self, payload):
        import os
        import shutil
        import subprocess
        import sys
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
            cmd = [
                str(updater),
                "--pid",
                str(os.getpid()),
                "--source",
                str(payload),
                "--target",
                str(target),
                "--restart-exe",
                str(target / "NOVA.exe"),
            ]
        else:
            target = Path(__file__).resolve().parent.parent
            updater_script = target / "nova_updater.py"
            cmd = [
                sys.executable,
                str(updater_script),
                "--pid",
                str(os.getpid()),
                "--source",
                str(payload),
                "--target",
                str(target),
                "--restart-exe",
                sys.executable,
                "--restart-arg",
                str(target / "main.py"),
                "--requirements",
                str(target / "requirements.txt"),
            ]
        subprocess.Popen(cmd, cwd=target)
        self.update_status.setText("NOVA를 종료하고 업데이트를 적용합니다...")
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
        ans = QMessageBox.question(
            self,
            "Reset paper account",
            "모의계좌, 주문, 규칙을 전부 초기화할까요?",
        )
        if ans == QMessageBox.StandardButton.Yes:
            self.db.reset_paper_account()
            self.current_quote = None
            self.refresh_all()
            self.statusBar().showMessage("Paper account reset")


def launch():
    app = QApplication.instance() or QApplication([])
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    w = MainWindow()
    w.show()
    return app.exec()
