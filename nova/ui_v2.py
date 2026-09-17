from __future__ import annotations

import pandas as pd
from PySide6.QtCore import QMargins, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCharts import QChart, QLineSeries, QValueAxis

from .config import APP_NAME, APP_VERSION
from . import ui as base


STYLE_V2 = r"""
QMainWindow, QWidget {
    background: #F7F7F8;
    color: #111111;
    font-family: "Segoe UI", "Malgun Gothic";
    font-size: 13px;
}

QFrame#AppHeader {
    background: #FFFFFF;
    border-bottom: 1px solid #ECECEF;
}
QFrame#PageHeader {
    background: transparent;
    border: none;
}
QFrame#Card {
    background: #FFFFFF;
    border: 1px solid #ECECEF;
    border-radius: 18px;
}
QFrame#HeroCard {
    background: #EEE8FF;
    border: none;
    border-radius: 24px;
}
QFrame#MetricCard {
    background: #FFFFFF;
    border: none;
    border-radius: 20px;
}
QFrame#MetricCard[tone="purple"] { background: #9B6BFF; }
QFrame#MetricCard[tone="blue"] { background: #29A9F6; }
QFrame#MetricCard[tone="soft"] { background: #ECECEF; }
QFrame#MetricCard[tone="dark"] { background: #171717; }
QFrame#DangerCard {
    background: #FFF0F2;
    border: none;
    border-radius: 20px;
}

QLabel#Brand {
    color: #111111;
    font-size: 26px;
    font-weight: 900;
    letter-spacing: -1px;
}
QLabel#BrandSub {
    color: #7E7E87;
    font-size: 10px;
    font-weight: 700;
}
QLabel#PageTitle {
    color: #111111;
    font-size: 31px;
    font-weight: 900;
    letter-spacing: -1px;
}
QLabel#Hero {
    color: #111111;
    font-size: 31px;
    font-weight: 900;
    letter-spacing: -1px;
}
QLabel#HeroSub {
    color: #5E5968;
    font-size: 13px;
}
QLabel#Muted { color: #777780; }
QLabel#Tiny { color: #92929A; font-size: 10px; }
QLabel#Section {
    color: #111111;
    font-size: 15px;
    font-weight: 800;
}
QLabel#MetricTitle {
    color: #7A7A83;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: .8px;
}
QLabel#Metric {
    color: #111111;
    font-size: 25px;
    font-weight: 900;
}
QLabel#MetricSmall { color: #8A8A92; font-size: 10px; }

QFrame#MetricCard[tone="purple"] QLabel,
QFrame#MetricCard[tone="blue"] QLabel,
QFrame#MetricCard[tone="dark"] QLabel {
    color: #FFFFFF;
}
QFrame#MetricCard[tone="purple"] QLabel#MetricTitle,
QFrame#MetricCard[tone="blue"] QLabel#MetricTitle,
QFrame#MetricCard[tone="dark"] QLabel#MetricTitle,
QFrame#MetricCard[tone="purple"] QLabel#MetricSmall,
QFrame#MetricCard[tone="blue"] QLabel#MetricSmall,
QFrame#MetricCard[tone="dark"] QLabel#MetricSmall {
    color: rgba(255,255,255,0.74);
}

QLabel#Badge {
    background: #EEE8FF;
    color: #6E3DDA;
    border: none;
    border-radius: 11px;
    padding: 5px 9px;
    font-size: 9px;
    font-weight: 800;
}
QLabel#BadgeGood {
    background: #E8F8EF;
    color: #147A49;
    border: none;
    border-radius: 11px;
    padding: 5px 9px;
    font-size: 9px;
    font-weight: 800;
}
QLabel#BadgeDanger {
    background: #FFE9ED;
    color: #C53C56;
    border: none;
    border-radius: 11px;
    padding: 5px 9px;
    font-size: 9px;
    font-weight: 800;
}

QPushButton {
    min-height: 22px;
    background: #FFFFFF;
    border: 1px solid #E3E3E8;
    border-radius: 12px;
    padding: 9px 14px;
    color: #111111;
    font-weight: 700;
}
QPushButton:hover {
    background: #F1F1F4;
    border-color: #D7D7DD;
}
QPushButton:pressed { background: #E9E9EE; }
QPushButton:disabled {
    background: #F4F4F6;
    border-color: #ECECEF;
    color: #B6B6BE;
}
QPushButton#Primary {
    background: #111111;
    border: none;
    color: #FFFFFF;
    font-weight: 800;
    padding: 10px 17px;
}
QPushButton#Primary:hover { background: #2A2A2A; }
QPushButton#Buy {
    background: #111111;
    border: none;
    color: #FFFFFF;
    font-weight: 800;
}
QPushButton#Buy:hover { background: #2A2A2A; }
QPushButton#Sell {
    background: #EEE8FF;
    border: none;
    color: #6F3EDC;
    font-weight: 800;
}
QPushButton#Sell:hover { background: #E3D9FF; }
QPushButton#Danger {
    background: #FFE8EC;
    border: none;
    color: #C93651;
    font-weight: 800;
    padding: 10px 14px;
}
QPushButton#Danger:hover { background: #FFDCE2; }
QPushButton#Danger:checked {
    background: #D83C59;
    color: white;
}

QPushButton#Nav {
    text-align: center;
    background: transparent;
    border: none;
    color: #85858D;
    padding: 8px 12px;
    border-radius: 10px;
    font-size: 12px;
    font-weight: 700;
}
QPushButton#Nav:hover {
    background: #F2F2F4;
    color: #111111;
}
QPushButton#Nav:checked {
    background: #111111;
    color: #FFFFFF;
}
QPushButton#Segment {
    background: transparent;
    border: none;
    color: #898991;
    padding: 7px 11px;
    border-radius: 10px;
}
QPushButton#Segment:checked {
    background: #111111;
    color: #FFFFFF;
}

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit {
    background: #FFFFFF;
    border: 1px solid #E6E6EA;
    border-radius: 12px;
    padding: 9px 11px;
    color: #111111;
    selection-background-color: #C7B4FF;
}
QLineEdit { min-height: 22px; }
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QComboBox:focus, QTextEdit:focus {
    border: 1px solid #9B6BFF;
}
QComboBox::drop-down { border: none; width: 25px; }

QProgressBar {
    background: rgba(0,0,0,0.08);
    border: none;
    border-radius: 4px;
    min-height: 7px;
    max-height: 7px;
    color: transparent;
}
QProgressBar::chunk { background: #7F4BFF; border-radius: 4px; }
QProgressBar#ConfidenceBar::chunk { background: #111111; }

QTableWidget {
    background: #FFFFFF;
    alternate-background-color: #FAFAFB;
    border: none;
    border-radius: 14px;
    gridline-color: transparent;
    outline: none;
    selection-background-color: #EEE8FF;
    selection-color: #111111;
}
QHeaderView::section {
    background: #FFFFFF;
    color: #8D8D96;
    border: none;
    border-bottom: 1px solid #ECECEF;
    padding: 10px 8px;
    font-size: 10px;
    font-weight: 800;
}
QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #F0F0F2;
}
QTableWidget::item:selected {
    background: #EEE8FF;
    color: #111111;
}

QScrollBar:vertical {
    background: transparent;
    width: 9px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: #D7D7DC;
    min-height: 28px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover { background: #BEBEC6; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }

QStatusBar {
    background: #FFFFFF;
    color: #8A8A92;
    border-top: 1px solid #ECECEF;
    min-height: 22px;
}
QToolTip {
    background: #111111;
    color: #FFFFFF;
    border: none;
    padding: 6px;
}
"""


class MainWindow(base.MainWindow):
    def __init__(self):
        base.STYLE = STYLE_V2
        super().__init__()
        self._apply_jitter_layout()

    def _build_ui(self):
        root = QWidget()
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QFrame()
        header.setObjectName("AppHeader")
        header.setFixedHeight(76)
        h = QHBoxLayout(header)
        h.setContentsMargins(28, 14, 28, 14)
        h.setSpacing(10)

        brand_box = QVBoxLayout()
        brand_box.setSpacing(0)
        brand = QLabel("NOVA")
        brand.setObjectName("Brand")
        sub = QLabel("PAPER INTELLIGENCE")
        sub.setObjectName("BrandSub")
        brand_box.addWidget(brand)
        brand_box.addWidget(sub)
        h.addLayout(brand_box)
        h.addSpacing(24)

        self.nav_buttons = []
        pages = [
            self._make_dashboard(),
            self._make_analysis(),
            self._make_trade(),
            self._make_rules(),
            self._make_safety(),
            self._make_updates(),
        ]
        nav_names = ["Portfolio", "Intelligence", "Trade", "Automation", "Risk", "System"]

        self.stack = QStackedWidget()
        for idx, (name, page) in enumerate(zip(nav_names, pages)):
            b = QPushButton(name)
            b.setObjectName("Nav")
            b.setCheckable(True)
            b.clicked.connect(lambda checked=False, i=idx: self._switch_page(i))
            self.nav_buttons.append(b)
            h.addWidget(b)
            self.stack.addWidget(page)
        self.nav_buttons[0].setChecked(True)

        h.addStretch(1)
        self.kill_badge = QLabel("Safety: checking...")
        self.kill_badge.setObjectName("BadgeGood")
        h.addWidget(self.kill_badge)
        self.top_safety_badge = QLabel("SIMULATION")
        self.top_safety_badge.setObjectName("Badge")
        h.addWidget(self.top_safety_badge)

        outer.addWidget(header)

        content = QWidget()
        content_l = QVBoxLayout(content)
        content_l.setContentsMargins(34, 26, 34, 22)
        content_l.setSpacing(18)

        page_header = QFrame()
        page_header.setObjectName("PageHeader")
        ph = QHBoxLayout(page_header)
        ph.setContentsMargins(0, 0, 0, 0)
        ph.setSpacing(0)
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.page_title_label = QLabel(self.page_meta[0][0])
        self.page_title_label.setObjectName("PageTitle")
        self.page_subtitle_label = QLabel(self.page_meta[0][1])
        self.page_subtitle_label.setObjectName("Muted")
        title_box.addWidget(self.page_title_label)
        title_box.addWidget(self.page_subtitle_label)
        ph.addLayout(title_box)
        ph.addStretch(1)
        version = QLabel(f"v{APP_VERSION}")
        version.setObjectName("Badge")
        ph.addWidget(version)

        content_l.addWidget(page_header)
        content_l.addWidget(self.stack, 1)
        outer.addWidget(content, 1)

        self.setCentralWidget(root)
        self.statusBar().showMessage("NOVA ready · simulation only")

    def _apply_jitter_layout(self):
        self.resize(1440, 900)
        self.setMinimumSize(1120, 740)
        self.menuBar().setVisible(False)

        self.page_meta = [
            ("Portfolio", "Your simulated account at a glance"),
            ("Intelligence", "ML signals, data quality and market context"),
            ("Trade", "Manual paper execution with safety checks"),
            ("Automation", "Price rules that you control"),
            ("Risk", "Hard limits, independent from AI"),
            ("System", "Updates, version and application status"),
        ]
        title, subtitle = self.page_meta[self.stack.currentIndex()]
        self.page_title_label.setText(title)
        self.page_subtitle_label.setText(subtitle)

        for button in self.nav_buttons:
            button.setMinimumWidth(88)
            button.setMinimumHeight(36)

        if hasattr(self, "analysis_ticker"):
            self.analysis_ticker.setPlaceholderText("Search ticker or company · 005930.KS · SK하이닉스 · AAPL")
        if hasattr(self, "analyze_btn"):
            self.analyze_btn.setText("Analyze")
            self.analyze_btn.setMinimumWidth(112)
        if hasattr(self, "easy_btn"):
            self.easy_btn.setText("Summary")
        if hasattr(self, "detail_btn"):
            self.detail_btn.setText("Deep dive")
        if hasattr(self, "quote_btn"):
            self.quote_btn.setText("Get quote")

        tones = ["purple", "blue", "soft", "dark"]
        for i, frame in enumerate(self.findChildren(QFrame, "MetricCard")):
            frame.setProperty("tone", tones[i % len(tones)])
            frame.style().unpolish(frame)
            frame.style().polish(frame)

        # Remove the old dark separator that was hard-coded inside the analysis card.
        for frame in self.findChildren(QFrame):
            if frame.maximumHeight() == 1 and frame.minimumHeight() == 1:
                frame.setStyleSheet("background:#ECECEF;border:none;")

        self.statusBar().showMessage("NOVA ready · paper trading environment")

    def _switch_page(self, index: int):
        super()._switch_page(index)
        title, subtitle = self.page_meta[index]
        self.page_title_label.setText(title)
        self.page_subtitle_label.setText(subtitle)

    def draw_chart(self, data: pd.DataFrame):
        frame = data.tail(120).copy()
        close = frame["Close"].astype(float)
        sma20 = close.rolling(20).mean()

        chart = QChart()
        chart.setBackgroundVisible(False)
        chart.setPlotAreaBackgroundVisible(True)
        chart.setPlotAreaBackgroundBrush(QColor("#F4F0FF"))
        chart.setMargins(QMargins(4, 6, 8, 4))
        chart.legend().setVisible(True)
        chart.legend().setLabelColor(QColor("#777780"))
        chart.legend().setFont(QFont("Segoe UI", 9))

        close_s = QLineSeries()
        close_s.setName("Price")
        close_s.setPen(QPen(QColor("#7F4BFF"), 2.6))

        sma_s = QLineSeries()
        sma_s.setName("SMA 20")
        sma_s.setPen(QPen(QColor("#29A9F6"), 1.8))

        for i, value in enumerate(close):
            close_s.append(i, float(value))
        for i, value in enumerate(sma20):
            if pd.notna(value):
                sma_s.append(i, float(value))

        chart.addSeries(close_s)
        chart.addSeries(sma_s)

        axis_x = QValueAxis()
        axis_x.setRange(0, max(1, len(frame) - 1))
        axis_x.setLabelsColor(QColor("#9A9AA2"))
        axis_x.setGridLineColor(QColor("#E6E0F5"))
        axis_x.setMinorGridLineVisible(False)
        axis_x.setTitleText("")

        axis_y = QValueAxis()
        lo = float(close.min()) * 0.985
        hi = float(close.max()) * 1.015
        axis_y.setRange(lo, hi)
        axis_y.setLabelFormat("%.0f")
        axis_y.setLabelsColor(QColor("#9A9AA2"))
        axis_y.setGridLineColor(QColor("#E6E0F5"))
        axis_y.setMinorGridLineVisible(False)

        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        close_s.attachAxis(axis_x)
        close_s.attachAxis(axis_y)
        sma_s.attachAxis(axis_x)
        sma_s.attachAxis(axis_y)
        self.chart_view.setChart(chart)


def launch():
    app = QApplication.instance() or QApplication([])
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    window = MainWindow()
    window.show()
    return app.exec()
