from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QProgressBar, QPushButton,
    QSpinBox, QComboBox, QDialog, QTextEdit,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from src.core.database import Database
from config.user_config import get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)

STATUS_COLORS = {
    "FOCUS": "#4caf50",
    "RELAX": "#5c6bc0",
    "DEVIATION": "#f44336",
    "UNKNOWN": "#888888",
}

STATUS_LABELS = {
    "FOCUS": "집중",
    "RELAX": "휴식",
    "DEVIATION": "이탈",
    "UNKNOWN": "알 수 없음",
}


class LogPanel(QWidget):
    """최근 정찰 기록 뷰어."""

    def __init__(self, db: Database):
        super().__init__()
        self._db = db
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Eye of Vera — 정찰 기록")
        self.setMinimumSize(560, 420)
        self.resize(620, 500)
        self._apply_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # ── 제목 ──
        title = QLabel("최근 정찰 기록")
        title.setFont(QFont("맑은 고딕", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # ── 오늘 요약 ──
        self._today_label = QLabel()
        self._today_label.setFont(QFont("맑은 고딕", 10))
        self._today_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._today_label)

        self._focus_bar = QProgressBar()
        self._focus_bar.setTextVisible(True)
        self._focus_bar.setFixedHeight(24)
        self._focus_bar.setStyleSheet("""
            QProgressBar { border: 1px solid #444; border-radius: 6px; background: #2e2e3e; text-align: center; color: white; }
            QProgressBar::chunk { background: #4caf50; border-radius: 5px; }
        """)
        layout.addWidget(self._focus_bar)

        # ── 조회 조건 ──
        ctrl_row = QHBoxLayout()

        ctrl_row.addWidget(QLabel("표시 건수:"))
        self._limit_spin = QSpinBox()
        self._limit_spin.setRange(5, 100)
        self._limit_spin.setValue(20)
        self._limit_spin.setSuffix(" 건")
        ctrl_row.addWidget(self._limit_spin)

        ctrl_row.addWidget(QLabel("필터:"))
        self._filter_combo = QComboBox()
        self._filter_combo.addItem("전체", "ALL")
        self._filter_combo.addItem("집중", "FOCUS")
        self._filter_combo.addItem("휴식", "RELAX")
        self._filter_combo.addItem("이탈", "DEVIATION")
        ctrl_row.addWidget(self._filter_combo)

        ctrl_row.addStretch()

        refresh_btn = QPushButton("새로고침")
        refresh_btn.setFixedWidth(90)
        refresh_btn.clicked.connect(self.refresh)
        ctrl_row.addWidget(refresh_btn)

        layout.addLayout(ctrl_row)

        # ── 로그 테이블 ──
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["시각", "상태", "감지된 활동", "베라 메시지"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.cellDoubleClicked.connect(self._show_detail)
        layout.addWidget(self._table, stretch=1)

        hint = QLabel("※ 행을 더블클릭하면 상세 내용을 볼 수 있습니다.")
        hint.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(hint)

    def _apply_style(self):
        theme = get_config().get_theme()
        self.setStyleSheet(
            f"QWidget {{ background: {theme['bg']}; color: {theme['text']}; }}"
            f"QPushButton {{ background: {theme['border']}; color: white; border: none; border-radius: 4px; padding: 6px 12px; font-weight: bold; }}"
            f"QPushButton:hover {{ background: {theme['hover']}; }}"
            f"QSpinBox, QComboBox {{ background: {theme['input_bg']}; color: {theme['text']}; border: 1px solid {theme['sub_border']}; border-radius: 4px; padding: 4px 8px; }}"
            f"QTableWidget {{ background: {theme['input_bg']}; gridline-color: {theme['sub_border']}; border: none; }}"
            f"QHeaderView::section {{ background: {theme['sub_border']}; color: {theme['text']}; padding: 6px; border: none; }}"
            f"QTableWidget::item {{ padding: 4px; }}"
            f"QTableWidget::item:selected {{ background: {theme['bg']}; }}"
        )

    def refresh(self):
        """데이터를 새로고침하여 표시."""
        # 오늘 요약
        today = self._db.get_daily_summary()
        self._today_label.setText(
            f"오늘 총 {today['total']}회 정찰  |  "
            f"집중 {today['focus']}  휴식 {today['relax']}  이탈 {today['deviation']}"
        )
        self._focus_bar.setValue(int(today["focus_rate"]))
        self._focus_bar.setFormat(f"집중률: {today['focus_rate']}%")

        # 로그 조회
        limit = self._limit_spin.value()
        status_filter = self._filter_combo.currentData()
        logs = self._db.get_recent_logs(limit)

        if status_filter != "ALL":
            logs = [log for log in logs if log["status"] == status_filter]

        self._cached_logs = logs

        # 테이블 채우기
        self._table.setRowCount(len(logs))
        for row, log in enumerate(logs):
            # 시각: "03-25 14:30" 형태
            ts = log["timestamp"]
            display_time = ts[5:16].replace("T", " ") if len(ts) >= 16 else ts

            self._table.setItem(row, 0, QTableWidgetItem(display_time))

            status = log["status"]
            status_item = QTableWidgetItem(STATUS_LABELS.get(status, status))
            status_item.setForeground(QColor(STATUS_COLORS.get(status, "#888")))
            self._table.setItem(row, 1, status_item)

            self._table.setItem(row, 2, QTableWidgetItem(log.get("detected_activity", "")))
            self._table.setItem(row, 3, QTableWidgetItem(log.get("message", "")))

        logger.info("정찰 기록 갱신 완료 (%d건)", len(logs))

    def _show_detail(self, row: int, _col: int):
        """행 더블클릭 시 상세 보기 다이얼로그."""
        if row < 0 or row >= len(self._cached_logs):
            return
        log = self._cached_logs[row]

        status = log["status"]
        ts = log["timestamp"]
        display_time = ts[:16].replace("T", " ") if len(ts) >= 16 else ts
        color = STATUS_COLORS.get(status, "#888")
        label = STATUS_LABELS.get(status, status)

        dlg = QDialog(self)
        dlg.setWindowTitle("정찰 상세 기록")
        dlg.setMinimumSize(440, 320)
        dlg.resize(480, 360)

        theme = get_config().get_theme()
        dlg.setStyleSheet(
            f"QDialog {{ background: {theme['bg']}; color: {theme['text']}; }}"
            f"QLabel {{ color: {theme['text']}; }}"
            f"QTextEdit {{ background: {theme['input_bg']}; color: {theme['text']}; "
            f"border: 1px solid {theme['sub_border']}; border-radius: 4px; padding: 8px; }}"
            f"QPushButton {{ background: {theme['border']}; color: white; border: none; "
            f"border-radius: 4px; padding: 8px 16px; font-weight: bold; }}"
            f"QPushButton:hover {{ background: {theme['hover']}; }}"
        )

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # 헤더: 시각 + 상태
        header = QLabel(f"{display_time}    <span style='color:{color};'>{label}</span>")
        header.setFont(QFont("맑은 고딕", 12, QFont.Weight.Bold))
        header.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(header)

        # 감지된 활동
        layout.addWidget(QLabel("감지된 활동:"))
        activity_text = QTextEdit()
        activity_text.setReadOnly(True)
        activity_text.setPlainText(log.get("detected_activity", ""))
        activity_text.setFont(QFont("Consolas", 10))
        layout.addWidget(activity_text, stretch=1)

        # 베라 메시지
        layout.addWidget(QLabel("베라 메시지:"))
        message_text = QTextEdit()
        message_text.setReadOnly(True)
        message_text.setPlainText(log.get("message", ""))
        message_text.setFont(QFont("맑은 고딕", 10))
        layout.addWidget(message_text, stretch=1)

        # 닫기 버튼
        close_btn = QPushButton("닫기")
        close_btn.setFixedWidth(80)
        close_btn.clicked.connect(dlg.close)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        dlg.exec()

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_style()
        self.refresh()
