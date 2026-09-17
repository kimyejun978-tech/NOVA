from __future__ import annotations

import pandas as pd
from PySide6.QtCore import QMargins, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QApplication, QFrame, QLabel, QPushButton
from PySide6.QtCharts import QChart, QLineSeries, QValueAxis

from .config import APP_NAME
from . import ui as base


STYLE_V2 = r"""
QMainWindow, QWidget {
    background: #070A0F;
    color: #E8EDF5;
    font-family: "Segoe UI", "Malgun Gothic";
    font-size: 13px;
}

QMenuBar {
    background: #070A0F;
    color: #778397;
    border-bottom: 1px solid #151B25;
    padding: 3px 8px;
}
QMenuBar::item:selected {
    background: #111824;
    color: #EAF0FA;
    border-radius: 6px;
}
QMenu {
    background: #0D121A;
    color: #E7ECF4;
    border: 1px solid #222C3A;
    padding: 6px;
}
QMenu::item { padding: 7px 16px; border-radius: 6px; }
QMenu::item:selected { background: #172235; }

QFrame#Sidebar {
    background: #090D14;
    border-right: 1px solid #18202C;
}
QFrame#TopBar {
    background: #090D14;
    border-bottom: 1px solid #18202C;
}

QFrame#Card {
    background: #0C1119;
    border: 1px solid #1C2532;
    border-radius: 12px;
}
QFrame#HeroCard {
    background: #0E1520;
    border: 1px solid #223149;
    border-radius: 14px;
}
QFrame#MetricCard {
    background: #0B1017;
    border: 1px solid #1B2532;
    border-radius: 11px;
}
QFrame#DangerCard {
    background: #140D12;
    border: 1px solid #41232D;
    border-radius: 12px;
}

QLabel#Brand {
    color: #F5F8FC;
    font-size: 27px;
    font-weight: 800;
    letter-spacing: 4px;
}
QLabel#BrandSub {
    color: #536176;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 2px;
}
QLabel#PageTitle {
    color: #F2F6FC;
    font-size: 21px;
    font-weight: 700;
}
QLabel#Hero {
    color: #F6F9FD;
    font-size: 27px;
    font-weight: 750;
}
QLabel#HeroSub { color: #7C899D; font-size: 12px; }
QLabel#Muted { color: #7A8798; }
QLabel#Tiny { color: #59677B; font-size: 10px; }
QLabel#Section {
    color: #DDE5F1;
    font-size: 14px;
    font-weight: 700;
}
QLabel#MetricTitle {
    color: #627087;
    font-size: 10px;
    font-weight: 750;
    letter-spacing: 1px;
}
QLabel#Metric {
    color: #F1F5FA;
    font-size: 24px;
    font-weight: 750;
}
QLabel#MetricSmall { color: #58667A; font-size: 10px; }

QLabel#Badge {
    background: #101B2B;
    color: #78A7FF;
    border: 1px solid #244166;
    border-radius: 8px;
    padding: 4px 8px;
    font-size: 9px;
    font-weight: 750;
}
QLabel#BadgeGood {
    background: #0D2119;
    color: #5ED39A;
    border: 1px solid #214838;
    border-radius: 8px;
    padding: 4px 8px;
    font-size: 9px;
    font-weight: 750;
}
QLabel#BadgeDanger {
    background: #271218;
    color: #FF7E8E;
    border: 1px solid #542832;
    border-radius: 8px;
    padding: 4px 8px;
    font-size: 9px;
    font-weight: 750;
}

QPushButton {
    min-height: 20px;
    background: #111824;
    border: 1px solid #263246;
    border-radius: 8px;
    padding: 8px 12px;
    color: #CFD7E5;
    font-weight: 600;
}
QPushButton:hover {
    background: #172235;
    border-color: #34445D;
    color: #F1F5FA;
}
QPushButton:pressed { background: #0D141F; }
QPushButton:disabled {
    background: #0D1219;
    border-color: #19212D;
    color: #465365;
}

QPushButton#Primary {
    background: #3478F6;
    border: 1px solid #3478F6;
    color: white;
    font-weight: 750;
}
QPushButton#Primary:hover {
    background: #4585FF;
    border-color: #4585FF;
}
QPushButton#Buy {
    background: #0F2C21;
    border: 1px solid #22543F;
    color: #67DCA2;
    font-weight: 750;
}
QPushButton#Buy:hover { background: #143B2C; }
QPushButton#Sell {
    background: #2A151C;
    border: 1px solid #5A2A38;
    color: #FF8596;
    font-weight: 750;
}
QPushButton#Sell:hover { background: #381B25; }
QPushButton#Danger {
    background: #251117;
    border: 1px solid #572A36;
    color: #FF8696;
    font-weight: 750;
    padding: 10px 13px;
}
QPushButton#Danger:hover { background: #341820; }
QPushButton#Danger:checked {
    background: #B3334B;
    border-color: #E04D66;
    color: white;
}

QPushButton#Nav {
    text-align: left;
    background: transparent;
    border: 1px solid transparent;
    color: #69778C;
    padding: 11px 12px;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 650;
}
QPushButton#Nav:hover {
    background: #0F1621;
    color: #C2CCDA;
}
QPushButton#Nav:checked {
    background: #111D2E;
    color: #E9F1FF;
    border: 1px solid #203A5E;
}
QPushButton#Segment {
    background: #0B1119;
    border: 1px solid #232E3D;
    color: #6E7C90;
    padding: 7px 11px;
    border-radius: 7px;
}
QPushButton#Segment:checked {
    background: #13233A;
    border-color: #2E5B91;
    color: #9DC2FF;
}

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit {
    background: #090E15;
    border: 1px solid #222D3C;
    border-radius: 8px;
    padding: 8px 10px;
    color: #E8EDF5;
    selection-background-color: #2C68C8;
}
QLineEdit { min-height: 22px; }
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QComboBox:focus, QTextEdit:focus {
    border: 1px solid #3979DA;
}
QComboBox::drop-down { border: none; width: 25px; }

QProgressBar {
    background: #070B11;
    border: 1px solid #1A2330;
    border-radius: 4px;
    min-height: 7px;
    max-height: 7px;
    color: transparent;
}
QProgressBar::chunk { background: #397EF7; border-radius: 3px; }
QProgressBar#ConfidenceBar::chunk { background: #49C58D; }

QTableWidget {
    background: #090E15;
    alternate-background-color: #0B111A;
    border: 1px solid #1B2532;
    border-radius: 9px;
    gridline-color: transparent;
    outline: none;
    selection-background-color: #12243D;
}
QHeaderView::section {
    background: #0D141E;
    color: #607087;
    border: none;
    border-bottom: 1px solid #202A38;
    padding: 9px 8px;
    font-size: 10px;
    font-weight: 750;
}
QTableWidget::item {
    padding: 7px;
    border-bottom: 1px solid #141C27;
}
QTableWidget::item:selected {
    background: #142742;
    color: #F4F7FC;
}

QScrollBar:vertical {
    background: transparent;
    width: 9px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: #263246;
    min-height: 28px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover { background: #34445D; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }

QStatusBar {
    background: #080C12;
    color: #566479;
    border-top: 1px solid #151D28;
    min-height: 23px;
}
QToolTip {
    background: #121A26;
    color: #E6ECF5;
    border: 1px solid #2B394D;
    padding: 5px;
}
"""


class MainWindow(base.MainWindow):
    def __init__(self):
        # base.MainWindow reads base.STYLE during construction.
        base.STYLE = STYLE_V2
        super().__init__()
        self._apply_terminal_layout()

    def _apply_terminal_layout(self):
        self.resize(1460, 900)
        self.setMinimumSize(1120, 740)

        # Cleaner desktop-app feel: navigation already exposes update controls.
        self.menuBar().setVisible(False)

        sidebar = self.findChild(QFrame, "Sidebar")
        if sidebar:
            sidebar.setFixedWidth(238)

        topbar = self.findChild(QFrame, "TopBar")
        if topbar:
            topbar.setFixedHeight(72)

        brands = self.findChildren(QLabel, "BrandSub")
        if brands:
            brands[0].setText("MARKET INTELLIGENCE")

        self.page_meta = [
            ("Portfolio", "Simulation balance, positions and recent activity"),
            ("Intelligence", "Hybrid market model and stock-specific analysis"),
            ("Trade", "Manual paper execution with hard safety checks"),
            ("Automation", "One-shot rules controlled by you"),
            ("Risk", "Non-AI limits and emergency controls"),
            ("System", "Version, updater and release status"),
        ]

        nav_labels = [
            "01   Portfolio",
            "02   Intelligence",
            "03   Trade",
            "04   Automation",
            "05   Risk",
            "06   System",
        ]
        for button, text in zip(self.nav_buttons, nav_labels):
            button.setText(text)
            button.setMinimumHeight(42)

        title, subtitle = self.page_meta[self.stack.currentIndex()]
        self.page_title_label.setText(title)
        self.page_subtitle_label.setText(subtitle)

        # Make the main action areas feel less like forms and more like a terminal.
        if hasattr(self, "analysis_ticker"):
            self.analysis_ticker.setPlaceholderText("Ticker / company · 005930.KS · SK하이닉스 · AAPL")
        if hasattr(self, "analyze_btn"):
            self.analyze_btn.setText("Analyze")
            self.analyze_btn.setMinimumWidth(110)
        if hasattr(self, "easy_btn"):
            self.easy_btn.setText("Summary")
        if hasattr(self, "detail_btn"):
            self.detail_btn.setText("Deep dive")
        if hasattr(self, "trade_ticker"):
            self.trade_ticker.setPlaceholderText("Ticker · 005930.KS · AAPL")
        if hasattr(self, "quote_btn"):
            self.quote_btn.setText("Get quote")

        self.statusBar().showMessage("NOVA terminal ready · simulation environment")

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
        chart.setPlotAreaBackgroundBrush(QColor("#090E15"))
        chart.setMargins(QMargins(4, 6, 8, 4))
        chart.legend().setVisible(True)
        chart.legend().setLabelColor(QColor("#718096"))
        chart.legend().setFont(QFont("Segoe UI", 9))

        close_s = QLineSeries()
        close_s.setName("Price")
        close_s.setPen(QPen(QColor("#4B8CFF"), 2.3))

        sma_s = QLineSeries()
        sma_s.setName("SMA 20")
        sma_s.setPen(QPen(QColor("#52C894"), 1.7))

        for i, value in enumerate(close):
            close_s.append(i, float(value))
        for i, value in enumerate(sma20):
            if pd.notna(value):
                sma_s.append(i, float(value))

        chart.addSeries(close_s)
        chart.addSeries(sma_s)

        axis_x = QValueAxis()
        axis_x.setRange(0, max(1, len(frame) - 1))
        axis_x.setLabelsColor(QColor("#566579"))
        axis_x.setGridLineColor(QColor("#18212D"))
        axis_x.setMinorGridLineVisible(False)
        axis_x.setTitleText("")

        axis_y = QValueAxis()
        lo = float(close.min()) * 0.985
        hi = float(close.max()) * 1.015
        axis_y.setRange(lo, hi)
        axis_y.setLabelFormat("%.0f")
        axis_y.setLabelsColor(QColor("#566579"))
        axis_y.setGridLineColor(QColor("#18212D"))
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
