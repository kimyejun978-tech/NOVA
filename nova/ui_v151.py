from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from .config import APP_NAME, APP_VERSION
from . import ui_v15 as previous


class MainWindow(previous.MainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — 모의투자 v{APP_VERSION}")
        self.statusBar().showMessage("NOVA · 모의투자 환경")

    def run_analysis(self):
        super().run_analysis()
        if hasattr(self, "analyze_btn") and not self.analyze_btn.isEnabled():
            self.analyze_btn.setText("분석 중...")

    def fetch_trade_quote(self):
        super().fetch_trade_quote()
        if hasattr(self, "quote_btn") and not self.quote_btn.isEnabled():
            self.trade_price.setText("시세 불러오는 중...")

    def _quote_done(self, q):
        super()._quote_done(q)
        if hasattr(self, "quote_btn"):
            self.quote_btn.setText("현재가 불러오기")
        self.statusBar().showMessage(f"{q.ticker} 시세를 불러왔습니다")

    def _quote_failed(self, msg):
        super()._quote_failed(msg)
        if hasattr(self, "quote_btn"):
            self.quote_btn.setText("현재가 불러오기")


def launch():
    app = QApplication.instance() or QApplication([])
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    window = MainWindow()
    window.show()
    return app.exec()
