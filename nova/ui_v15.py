from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QFrame, QLabel, QGraphicsDropShadowEffect

from .config import APP_NAME
from . import ui_v2 as previous


STYLE_PATCH = r"""
/* 1.5 polish: keep labels transparent inside tinted cards. */
QLabel {
    background: transparent;
    border: none;
}

QMainWindow, QWidget {
    background: #F7F7F8;
}

QFrame#AppHeader {
    background: #FFFFFF;
    border-bottom: 1px solid #EEEEF1;
}
QFrame#PageHeader {
    background: transparent;
}

QFrame#HeroCard {
    background: #EEE8FF;
    border: none;
    border-radius: 26px;
}
QFrame#Card {
    background: #FFFFFF;
    border: 1px solid #ECECF0;
    border-radius: 20px;
}
QFrame#MetricCard {
    border: none;
    border-radius: 22px;
}
QFrame#MetricCard[tone="purple"] { background: #8B5CF6; }
QFrame#MetricCard[tone="blue"] { background: #2D9CDB; }
QFrame#MetricCard[tone="soft"] { background: #ECECF0; }
QFrame#MetricCard[tone="dark"] { background: #18181B; }

QFrame#HeroCard QLabel,
QFrame#MetricCard QLabel,
QFrame#Card QLabel,
QFrame#DangerCard QLabel {
    background: transparent;
}

QLabel#Brand {
    font-size: 27px;
    font-weight: 900;
    color: #111111;
}
QLabel#BrandSub {
    color: #8A8A93;
    font-size: 9px;
    font-weight: 700;
}
QLabel#PageTitle {
    font-size: 32px;
    font-weight: 900;
    color: #111111;
}
QLabel#Hero {
    font-size: 30px;
    font-weight: 900;
    color: #111111;
}
QLabel#HeroSub {
    color: #65616E;
    font-size: 13px;
}
QLabel#Section {
    font-size: 15px;
    font-weight: 800;
    color: #151515;
}
QLabel#Muted { color: #767680; }
QLabel#Tiny { color: #9999A2; font-size: 10px; }
QLabel#MetricTitle {
    color: #777781;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: .7px;
}
QLabel#Metric {
    color: #111111;
    font-size: 27px;
    font-weight: 900;
}
QLabel#MetricSmall { color: #898992; font-size: 10px; }

QFrame#MetricCard[tone="purple"] QLabel,
QFrame#MetricCard[tone="blue"] QLabel,
QFrame#MetricCard[tone="dark"] QLabel {
    color: #FFFFFF;
    background: transparent;
}
QFrame#MetricCard[tone="purple"] QLabel#MetricTitle,
QFrame#MetricCard[tone="blue"] QLabel#MetricTitle,
QFrame#MetricCard[tone="dark"] QLabel#MetricTitle,
QFrame#MetricCard[tone="purple"] QLabel#MetricSmall,
QFrame#MetricCard[tone="blue"] QLabel#MetricSmall,
QFrame#MetricCard[tone="dark"] QLabel#MetricSmall {
    color: rgba(255,255,255,0.76);
}

QPushButton#Nav {
    min-height: 34px;
    padding: 7px 14px;
    border-radius: 11px;
    font-weight: 700;
}
QPushButton#Nav:hover {
    background: #F3F3F5;
    color: #111111;
}
QPushButton#Nav:checked {
    background: #111111;
    color: #FFFFFF;
}
QPushButton#Primary {
    background: #111111;
    color: #FFFFFF;
    border: none;
    border-radius: 13px;
    padding: 10px 17px;
}
QPushButton#Primary:hover { background: #292929; }
QPushButton {
    border-radius: 13px;
}

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit {
    background: #FFFFFF;
    border: 1px solid #E6E6EA;
    border-radius: 13px;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QComboBox:focus, QTextEdit:focus {
    border: 1px solid #8B5CF6;
}

QTableWidget {
    background: #FFFFFF;
    border: none;
    border-radius: 16px;
}
QHeaderView::section {
    background: #FFFFFF;
    border: none;
    border-bottom: 1px solid #EEEEF1;
    color: #909099;
    padding: 11px 8px;
}
QTableWidget::item {
    background: transparent;
    border-bottom: 1px solid #F1F1F3;
    padding: 9px 8px;
}
QTableWidget::item:selected {
    background: #EEE8FF;
    color: #111111;
}

QStatusBar {
    background: #FFFFFF;
    color: #9A9AA2;
    border-top: 1px solid #EEEEF1;
}
"""


class MainWindow(previous.MainWindow):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(previous.STYLE_V2 + STYLE_PATCH)
        self._apply_v15_polish()

    def _apply_v15_polish(self):
        self.resize(1480, 900)
        self.setMinimumSize(1160, 760)

        # Keep a single safety indicator in the header.
        if hasattr(self, "top_safety_badge"):
            self.top_safety_badge.hide()

        # Remove the floating version pill from the generic page header.
        page_header = self.findChild(QFrame, "PageHeader")
        if page_header:
            for label in page_header.findChildren(QLabel):
                if label.text().strip().lower().startswith("v"):
                    label.hide()

        app_header = self.findChild(QFrame, "AppHeader")
        if app_header:
            app_header.setFixedHeight(72)

        # Make the dashboard cards consistent and deliberate.
        dashboard_cards = [
            getattr(self, "equity_card", None),
            getattr(self, "cash_card", None),
            getattr(self, "invested_card", None),
            getattr(self, "pos_card", None),
        ]
        tones = ["purple", "blue", "soft", "dark"]
        for frame, tone in zip(dashboard_cards, tones):
            if not frame:
                continue
            frame.setProperty("tone", tone)
            frame.setMinimumHeight(116)
            frame.setMaximumHeight(132)
            frame.style().unpolish(frame)
            frame.style().polish(frame)

        # Slightly more breathing room on the high-value summary cards.
        for frame in self.findChildren(QFrame, "HeroCard"):
            frame.setMinimumHeight(118)

        # Subtle depth only for neutral white cards, not for the bright metric cards.
        for frame in self.findChildren(QFrame, "Card"):
            shadow = QGraphicsDropShadowEffect(frame)
            shadow.setBlurRadius(22)
            shadow.setOffset(0, 4)
            from PySide6.QtGui import QColor
            shadow.setColor(QColor(0, 0, 0, 16))
            frame.setGraphicsEffect(shadow)

        if hasattr(self, "kill_badge"):
            self.kill_badge.setText("Safety armed")

        self.statusBar().showMessage("NOVA · paper trading environment")

    def refresh_safety(self):
        super().refresh_safety()
        # Base refresh still updates the hidden duplicate badge for compatibility.
        if hasattr(self, "top_safety_badge"):
            self.top_safety_badge.hide()


def launch():
    app = QApplication.instance() or QApplication([])
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    window = MainWindow()
    window.show()
    return app.exec()
