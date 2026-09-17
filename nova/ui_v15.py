from __future__ import annotations

from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QLabel,
    QPushButton,
    QGraphicsDropShadowEffect,
)

from .config import APP_NAME
from . import ui_v2 as previous


STYLE_PATCH = r"""
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


LABEL_TRANSLATIONS = {
    "PAPER INTELLIGENCE": "모의투자 분석",
    "Paper portfolio": "모의 포트폴리오",
    "실계좌와 완전히 분리된 모의 자동매매 환경": "실계좌와 완전히 분리된 모의투자·자동매매 환경",
    "Market data can be delayed. NOVA v1 never sends live brokerage orders.": "시세 데이터는 지연될 수 있으며, NOVA는 실제 증권사 주문을 전송하지 않습니다.",
    "PAPER EQUITY": "모의자산",
    "CASH": "현금",
    "INVESTED": "투자금액",
    "POSITIONS": "보유종목",
    "cash + position book value": "현금 + 보유자산 장부가",
    "available simulation balance": "사용 가능한 모의잔고",
    "position book value": "보유자산 장부가",
    "open simulated holdings": "현재 보유 종목 수",
    "Open positions": "보유 포지션",
    "Recent activity": "최근 거래",
    "Stock intelligence": "종목 AI 분석",
    "Global Model + stock-specific Model + Data Guard": "전체시장 모델 + 종목 전용 모델 + 데이터 검증",
    "UP PROBABILITY": "상승 확률",
    "REFERENCE RANGE": "예상 가격 범위",
    "CONFIDENCE": "신뢰도",
    "DATA TIER": "데이터 등급",
    "model-estimated interval": "모델이 계산한 예상 범위",
    "Data Guard availability": "데이터 품질과 사용 가능성",
    "NOVA advisory": "NOVA 분석 의견",
    "ADVISORY ONLY": "권고 전용",
    "Strategy note": "전략 참고",
    "Price context": "가격 흐름",
    "CLOSE + SMA20": "종가 + SMA20",
    "Order ticket": "모의 주문",
    "PAPER ONLY": "모의거래 전용",
    "LAST PRICE": "현재가",
    "No quote loaded": "시세를 불러오지 않았습니다",
    "Quantity": "수량",
    "Execution rules": "체결 원칙",
    "NOVA never routes this ticket to a real broker.": "NOVA는 이 주문을 실제 증권사로 전송하지 않습니다.",
    "PRICE": "가격",
    "Uses the last loaded market quote": "마지막으로 불러온 시세를 사용합니다",
    "SAFETY": "안전장치",
    "Order value, position weight and cooldown are checked": "주문금액·종목비중·연속주문 제한을 검사합니다",
    "AI": "AI",
    "Can explain or suggest, but cannot submit or edit orders": "설명과 권고만 가능하며 주문 실행·수정 권한은 없습니다",
    "PERSISTENCE": "저장",
    "Paper fills are saved locally in NOVA's database": "모의 체결 내역은 NOVA 로컬 DB에 저장됩니다",
    "Order history": "주문 내역",
    "SIMULATED FILLS": "모의 체결",
    "Rule builder": "자동매매 규칙 만들기",
    "ONE-SHOT": "1회 실행",
    "Ticker": "종목",
    "Condition": "조건",
    "Trigger": "기준가",
    "Action": "동작",
    "Permission boundary": "AI 권한 제한",
    "AI CANNOT EDIT RULES": "AI는 규칙을 수정할 수 없음",
    "Only rules created or changed by you can become executable.": "사용자가 직접 만들거나 변경한 규칙만 실행할 수 있습니다.",
    "AI recommendations stay advisory and never write into this rule table.": "AI의 제안은 권고로만 표시되며 자동매매 규칙을 직접 변경하지 않습니다.",
    "Active automation": "활성 자동매매 규칙",
    "Emergency trading lock": "긴급 거래 잠금",
    "Hard safety switch independent from ML and AI": "ML·AI와 독립적으로 동작하는 하드 안전장치",
    "When enabled, every new simulated BUY/SELL is blocked. Existing positions are kept.": "켜면 새로운 모의 매수·매도가 모두 차단되며 기존 보유종목은 유지됩니다.",
    "Risk limits": "거래 안전 한도",
    "Max order value": "1회 최대 주문금액",
    "Max position weight": "종목 최대 비중",
    "Same ticker cooldown": "동일 종목 재주문 대기",
    "Safety architecture": "안전 구조",
    "HARD-CODED GATE": "강제 안전 게이트",
    "Manual order → Safety Engine → Paper Broker": "수동 주문 → 안전 엔진 → 모의 브로커",
    "Rule trigger → Safety Engine → Paper Broker": "자동 규칙 → 안전 엔진 → 모의 브로커",
    "AI advisory has no broker or rule mutation permission.": "AI 권고 기능에는 주문·규칙 변경 권한이 없습니다.",
    "Reset simulation": "모의계좌 초기화",
    "NOVA Update": "NOVA 업데이트",
    "Release status": "업데이트 상태",
    "RELEASE NOTES": "업데이트 내용",
    "Update packages are SHA-256 verified before the standalone updater replaces NOVA. Local paper-trading data is preserved.": "업데이트 파일은 SHA-256 검증 후 적용되며 모의계좌 데이터는 그대로 유지됩니다.",
}

BUTTON_TRANSLATIONS = {
    "Analyze stock": "종목 분석",
    "New paper order": "모의 주문",
    "Summary": "요약",
    "Deep dive": "상세 보기",
    "Analyze": "분석하기",
    "Run analysis": "분석하기",
    "Get quote": "현재가 불러오기",
    "Load price": "현재가 불러오기",
    "BUY · PAPER": "모의 매수",
    "SELL · PAPER": "모의 매도",
    "Create rule": "규칙 만들기",
    "Scan now": "지금 검사",
    "Enable / Disable": "켜기 / 끄기",
    "Delete selected": "선택 삭제",
    "Save safety limits": "안전 한도 저장",
    "Reset paper account": "모의계좌 초기화",
    "Check for updates": "업데이트 확인",
    "Update & restart": "업데이트 후 재시작",
}


class MainWindow(previous.MainWindow):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(previous.STYLE_V2 + STYLE_PATCH)
        self._apply_v15_polish()
        self._apply_korean_locale()

    def _apply_v15_polish(self):
        self.resize(1480, 900)
        self.setMinimumSize(1160, 760)

        if hasattr(self, "top_safety_badge"):
            self.top_safety_badge.hide()

        page_header = self.findChild(QFrame, "PageHeader")
        if page_header:
            for label in page_header.findChildren(QLabel):
                if label.text().strip().lower().startswith("v"):
                    label.hide()

        app_header = self.findChild(QFrame, "AppHeader")
        if app_header:
            app_header.setFixedHeight(72)

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

        for frame in self.findChildren(QFrame, "HeroCard"):
            frame.setMinimumHeight(118)

        for frame in self.findChildren(QFrame, "Card"):
            shadow = QGraphicsDropShadowEffect(frame)
            shadow.setBlurRadius(22)
            shadow.setOffset(0, 4)
            shadow.setColor(QColor(0, 0, 0, 16))
            frame.setGraphicsEffect(shadow)

        self.refresh_safety()

    def _apply_korean_locale(self):
        self.page_meta = [
            ("포트폴리오", "모의계좌와 보유 포지션을 한눈에 확인합니다"),
            ("AI 분석", "ML 예측·데이터 품질·시장 흐름을 종합 분석합니다"),
            ("모의매매", "안전장치를 거쳐 가상 자금으로 주문을 실행합니다"),
            ("자동화", "사용자가 직접 설정한 가격 조건만 자동 실행합니다"),
            ("안전", "AI와 독립된 거래 제한과 긴급 잠금을 관리합니다"),
            ("설정", "버전과 자동 업데이트 상태를 관리합니다"),
        ]
        nav_names = ["포트폴리오", "AI 분석", "모의매매", "자동화", "안전", "설정"]
        for button, text in zip(self.nav_buttons, nav_names):
            button.setText(text)

        current = self.stack.currentIndex()
        self.page_title_label.setText(self.page_meta[current][0])
        self.page_subtitle_label.setText(self.page_meta[current][1])

        for label in self.findChildren(QLabel):
            text = label.text()
            if text in LABEL_TRANSLATIONS:
                label.setText(LABEL_TRANSLATIONS[text])
            elif text.startswith("CURRENT ·"):
                label.setText(text.replace("CURRENT", "현재 버전", 1))
            elif text.startswith("Current version:"):
                label.setText(text.replace("Current version:", "현재 버전:", 1))
            elif text.startswith("Auto scan · every "):
                seconds = text.removeprefix("Auto scan · every ").removesuffix("s")
                label.setText(f"자동 검사 · {seconds}초마다")

        for button in self.findChildren(QPushButton):
            if button.text() in BUTTON_TRANSLATIONS:
                button.setText(BUTTON_TRANSLATIONS[button.text()])

        if hasattr(self, "analysis_ticker"):
            self.analysis_ticker.setPlaceholderText("종목명 또는 종목코드 검색 · 삼성전자 · SK하이닉스 · 005930.KS · AAPL")
        if hasattr(self, "horizon"):
            horizon_texts = ["1일", "1주", "1개월"]
            for i, text in enumerate(horizon_texts):
                if i < self.horizon.count():
                    self.horizon.setItemText(i, text)
        if hasattr(self, "trade_ticker"):
            self.trade_ticker.setPlaceholderText("종목명 또는 종목코드 · 삼성전자 · 005930.KS · AAPL")

        if hasattr(self, "positions_table"):
            self.positions_table.setHorizontalHeaderLabels(["종목", "수량", "평균단가", "장부가", "업데이트"])
        if hasattr(self, "orders_table"):
            self.orders_table.setHorizontalHeaderLabels(["시간", "종목", "구분", "수량", "가격", "출처", "상태"])
        if hasattr(self, "trade_orders"):
            self.trade_orders.setHorizontalHeaderLabels(["시간", "종목", "구분", "수량", "가격", "총액", "출처", "상태"])
        if hasattr(self, "rules_table"):
            self.rules_table.setHorizontalHeaderLabels(["ID", "종목", "조건", "기준가", "동작", "수량", "사용", "최근 실행"])

        if hasattr(self, "analysis_text"):
            self.analysis_text.setPlaceholderText("종목을 분석하면 NOVA의 설명이 여기에 표시됩니다.")
        if hasattr(self, "update_current"):
            self.update_current.setText(self.update_current.text().replace("Current version:", "현재 버전:"))

        self.refresh_safety()
        self.statusBar().showMessage("NOVA · 모의투자 환경")

    def _switch_page(self, index: int):
        super()._switch_page(index)
        if 0 <= index < len(self.page_meta):
            title, subtitle = self.page_meta[index]
            self.page_title_label.setText(title)
            self.page_subtitle_label.setText(subtitle)

    def refresh_safety(self):
        super().refresh_safety()
        if not hasattr(self, "kill_switch"):
            return
        on = self.db.get_setting("kill_switch", "0") == "1"
        self.kill_switch.setText("긴급 정지 ON" if on else "긴급 정지 OFF")
        if hasattr(self, "kill_badge"):
            self.kill_badge.setText("안전장치: 잠금" if on else "안전장치: 정상")
        if hasattr(self, "top_safety_badge"):
            self.top_safety_badge.hide()

    def render_analysis(self):
        super().render_analysis()
        if hasattr(self, "analyze_btn"):
            self.analyze_btn.setText("분석하기")


def launch():
    app = QApplication.instance() or QApplication([])
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    window = MainWindow()
    window.show()
    return app.exec()
