from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from .config import APP_NAME, APP_VERSION
from .recommender import Candidate, RecommendationEngine, RecommendationResult
from . import ui_v151 as previous


class RecommendationDialog(QDialog):
    def __init__(self, owner: "MainWindow"):
        super().__init__(owner)
        self.owner = owner
        self.engine = RecommendationEngine(owner.market)
        self.results: list[Candidate] = []

        self.setWindowTitle("NOVA · AI 종목 후보 탐색")
        self.resize(1240, 720)
        self.setMinimumSize(980, 620)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 22)
        root.setSpacing(14)

        head = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("AI 종목 후보 탐색")
        title.setObjectName("Hero")
        sub = QLabel("시장 데이터를 스크리닝해 모의투자 연구 후보를 찾습니다.")
        sub.setObjectName("HeroSub")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        head.addLayout(title_box)
        head.addStretch(1)

        safe = QLabel("모의투자 연구용")
        safe.setObjectName("BadgeGood")
        head.addWidget(safe)
        root.addLayout(head)

        notice = QFrame()
        notice.setObjectName("HeroCard")
        notice_l = QHBoxLayout(notice)
        notice_l.setContentsMargins(18, 13, 18, 13)
        notice_text = QLabel(
            "후보 탐색 결과는 과거 가격·거래량 패턴을 이용한 연구용 결과입니다. "
            "실제 매수 주문이나 자동매매 규칙으로 직접 연결되지 않습니다."
        )
        notice_text.setWordWrap(True)
        notice_text.setObjectName("Muted")
        notice_l.addWidget(notice_text)
        root.addWidget(notice)

        controls = QFrame()
        controls.setObjectName("Card")
        c = QHBoxLayout(controls)
        c.setContentsMargins(16, 14, 16, 14)
        c.setSpacing(10)

        c.addWidget(QLabel("시장"))
        self.market_combo = QComboBox()
        self.market_combo.addItem("한국", "KR")
        self.market_combo.addItem("미국", "US")
        c.addWidget(self.market_combo)

        c.addWidget(QLabel("전망 기간"))
        self.horizon_combo = QComboBox()
        self.horizon_combo.addItem("1일", 1)
        self.horizon_combo.addItem("1주", 5)
        self.horizon_combo.addItem("1개월", 20)
        self.horizon_combo.setCurrentIndex(1)
        c.addWidget(self.horizon_combo)

        c.addWidget(QLabel("후보 수"))
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(3, 10)
        self.limit_spin.setValue(5)
        c.addWidget(self.limit_spin)

        c.addWidget(QLabel("최소 신뢰도"))
        self.conf_spin = QSpinBox()
        self.conf_spin.setRange(30, 85)
        self.conf_spin.setValue(45)
        self.conf_spin.setSuffix("%")
        c.addWidget(self.conf_spin)

        c.addStretch(1)
        self.scan_btn = QPushButton("후보 찾기")
        self.scan_btn.setObjectName("Primary")
        self.scan_btn.clicked.connect(self.scan)
        c.addWidget(self.scan_btn)
        root.addWidget(controls)

        self.status_label = QLabel("시장과 전망 기간을 선택한 뒤 후보 찾기를 눌러주세요.")
        self.status_label.setObjectName("Muted")
        root.addWidget(self.status_label)

        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels([
            "순위", "종목", "상승 확률", "신뢰도", "위험",
            "현재가", "예상 범위", "데이터", "탐색 점수", "주요 근거",
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)
        header = self.table.horizontalHeader()
        for col in range(9):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.Stretch)
        self.table.doubleClicked.connect(self.open_selected)
        root.addWidget(self.table, 1)

        foot = QHBoxLayout()
        self.model_info = QLabel("")
        self.model_info.setObjectName("Tiny")
        foot.addWidget(self.model_info)
        foot.addStretch(1)
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.close)
        self.detail_btn = QPushButton("선택 종목 상세 분석")
        self.detail_btn.setObjectName("Primary")
        self.detail_btn.setEnabled(False)
        self.detail_btn.clicked.connect(self.open_selected)
        foot.addWidget(close_btn)
        foot.addWidget(self.detail_btn)
        root.addLayout(foot)

        self.table.itemSelectionChanged.connect(
            lambda: self.detail_btn.setEnabled(self.table.currentRow() >= 0)
        )

    def scan(self):
        market = str(self.market_combo.currentData())
        horizon = int(self.horizon_combo.currentData())
        limit = int(self.limit_spin.value())
        min_conf = float(self.conf_spin.value()) / 100.0

        self.scan_btn.setEnabled(False)
        self.detail_btn.setEnabled(False)
        self.table.setRowCount(0)
        self.results = []
        self.status_label.setText(
            "데이터 수집 → Data Guard → 시장 ML → 상위 후보 정밀 분석을 진행 중입니다. "
            "첫 실행은 데이터 다운로드 때문에 시간이 조금 걸릴 수 있습니다."
        )
        self.model_info.setText("")

        def task():
            return self.engine.scan(
                market_code=market,
                horizon_days=horizon,
                limit=limit,
                min_confidence=min_conf,
            )

        self.owner.run_task(task, self._scan_done, self._scan_failed)

    def _scan_done(self, result: RecommendationResult):
        self.scan_btn.setEnabled(True)
        self.results = result.candidates
        self._render(result)

    def _scan_failed(self, message: str):
        self.scan_btn.setEnabled(True)
        self.status_label.setText("후보 탐색에 실패했습니다.")
        QMessageBox.warning(self, "NOVA", message)

    @staticmethod
    def _item(text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        return item

    def _render(self, result: RecommendationResult):
        if not result.candidates:
            self.table.setRowCount(0)
            self.status_label.setText(
                "현재 설정한 신뢰도와 데이터 기준을 통과한 후보가 없습니다. "
                "NOVA는 조건이 약할 때 억지로 종목을 추천하지 않습니다."
            )
        else:
            self.status_label.setText(
                f"{result.scanned}개 종목 중 {result.usable}개를 분석했고, "
                f"조건을 통과한 상위 {len(result.candidates)}개 연구 후보를 표시합니다."
            )

        self.model_info.setText(
            f"시장 스크리너 검증 정확도 {result.global_accuracy * 100:.1f}% · "
            f"Brier {result.global_brier:.3f} · 실제 수익 보장 지표가 아닙니다."
        )

        self.table.setRowCount(len(result.candidates))
        kr = result.market == "KR"
        for row, x in enumerate(result.candidates):
            current = f"₩{x.current_price:,.0f}" if kr else f"${x.current_price:,.2f}"
            low = f"₩{x.expected_low_price:,.0f}" if kr else f"${x.expected_low_price:,.2f}"
            high = f"₩{x.expected_high_price:,.0f}" if kr else f"${x.expected_high_price:,.2f}"
            values = [
                str(row + 1),
                f"{x.name}\n{x.ticker}",
                f"{x.up_probability * 100:.1f}%",
                f"{x.confidence * 100:.0f}%",
                x.risk,
                current,
                f"{low} ~ {high}",
                f"{x.data_tier} · {x.data_quality * 100:.0f}",
                f"{x.score:.1f}",
                x.reason,
            ]
            for col, value in enumerate(values):
                self.table.setItem(row, col, self._item(value))

        if result.candidates:
            self.table.selectRow(0)
            self.detail_btn.setEnabled(True)

    def open_selected(self, *_args):
        row = self.table.currentRow()
        if row < 0 or row >= len(self.results):
            return
        ticker = self.results[row].ticker
        self.owner._switch_page(1)
        self.owner.analysis_ticker.setText(ticker)
        self.close()
        self.owner.run_analysis()


class MainWindow(previous.MainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — 모의투자 v{APP_VERSION}")
        self._recommend_dialog: RecommendationDialog | None = None
        self._install_recommend_button()

    def _install_recommend_button(self):
        header = self.findChild(QFrame, "AppHeader")
        if not header or not self.nav_buttons:
            return

        button = QPushButton("종목 탐색")
        button.setObjectName("Nav")
        button.clicked.connect(self.open_recommender)

        layout = header.layout()
        analysis_button = self.nav_buttons[1]
        index = layout.indexOf(analysis_button)
        if index >= 0:
            layout.insertWidget(index + 1, button)
        else:
            layout.addWidget(button)
        self.recommend_nav_button = button

    def open_recommender(self):
        if self._recommend_dialog is None:
            self._recommend_dialog = RecommendationDialog(self)
        self._recommend_dialog.show()
        self._recommend_dialog.raise_()
        self._recommend_dialog.activateWindow()


def launch():
    app = QApplication.instance() or QApplication([])
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    window = MainWindow()
    window.show()
    return app.exec()
