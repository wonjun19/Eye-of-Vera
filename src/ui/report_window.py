from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QProgressBar, QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from src.core.database import Database
from src.ui.design import FONT_MONO, FONT_UI, scrollbar_style
from config.user_config import get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)

_STATUS_COLS = {
    "FOCUS":     "#43a047",
    "RELAX":     "#5c6bc0",
    "DEVIATION": "#e53935",
}


class ReportWindow(QWidget):
    """주간 결산 리포트 창 — VERA-OS v2.

    블록 구조:
      ┌─ Title ─────────────────────────────────┐
      ├─ Today Summary ─────────────────────────┤
      │  집중률 Progress Bar                    │
      ├─ Separator ─────────────────────────────┤
      ├─ Weekly Table ──────────────────────────┤
      │  날짜 / FOCUS / RELAX / DEVIATION / 집중률 │
      └─────────────────────────────────────────┘
    """

    def __init__(self, db: Database):
        super().__init__()
        self._db = db
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Eye of Vera — 주간 결산")
        self.setMinimumSize(540, 440)
        self.resize(580, 500)
        self._apply_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)

        # ── Title Block ──
        title_row = QHBoxLayout()
        title = QLabel("주간 작전 결산")
        title.setFont(QFont(FONT_MONO, 13, QFont.Weight.Bold))
        title_row.addWidget(title)
        title_row.addStretch()
        self._period_label = QLabel("")
        self._period_label.setFont(QFont(FONT_MONO, 9))
        title_row.addWidget(self._period_label)
        layout.addLayout(title_row)

        # ── Today Summary Block ──
        self._today_label = QLabel()
        self._today_label.setFont(QFont(FONT_UI, 10))
        self._today_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._today_label)

        self._focus_bar = QProgressBar()
        self._focus_bar.setTextVisible(True)
        self._focus_bar.setFixedHeight(24)
        self._focus_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #1a3a1a;
                border-radius: 7px;
                background: #0a0f0a;
                text-align: center;
                color: #c8e6c9;
                font-family: Consolas;
                font-size: 9pt;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #1b5e20, stop:0.45 #43a047,
                    stop:0.55 #43a047, stop:1 #1b5e20);
                border-radius: 6px;
            }
        """)
        layout.addWidget(self._focus_bar)

        # ── Separator ──
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        # ── Weekly Table Block ──
        week_title = QLabel("7일 상세")
        week_title.setFont(QFont(FONT_MONO, 9))
        layout.addWidget(week_title)

        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["날짜", "집중", "휴식", "이탈", "집중률"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table, stretch=1)

    def _apply_style(self):
        t = get_config().get_theme()
        self.setStyleSheet(
            f"QWidget {{ background: {t['bg']}; color: {t['text']}; }}"
            f"QLabel {{ color: {t['text']}; }}"
            f"QFrame {{ color: {t['sub_border']}; }}"
            f"QTableWidget {{"
            f"  background: {t['input_bg']}; alternate-background-color: {t['bg']};"
            f"  border: 1px solid {t['sub_border']}; border-radius: 6px;"
            f"}}"
            f"QHeaderView::section {{"
            f"  background: {t['sub_border']}; color: {t['text']};"
            f"  padding: 8px; border: none; font-family: Consolas; font-size: 9pt;"
            f"}}"
            f"QTableWidget::item {{ padding: 6px; }}"
            + scrollbar_style(t["input_bg"], t["border"])
        )

    def refresh(self):
        """데이터 새로고침."""
        t = get_config().get_theme()

        # 오늘 요약
        today = self._db.get_daily_summary()
        self._today_label.setText(
            f"오늘  집중 {today['focus']}회 · 휴식 {today['relax']}회 · 이탈 {today['deviation']}회"
            f"  /  총 {today['total']}회"
        )
        self._today_label.setStyleSheet(f"color: {t['text']}99;")

        self._focus_bar.setValue(int(today["focus_rate"]))
        self._focus_bar.setFormat(f"오늘 집중률  {today['focus_rate']}%")

        # 주간 테이블
        weekly = self._db.get_weekly_summary()
        self._table.setRowCount(len(weekly))

        if weekly:
            start = weekly[-1]["date"]
            end   = weekly[0]["date"]
            self._period_label.setText(f"{start} – {end}")
            self._period_label.setStyleSheet(f"color: {t['text']}66;")

        for row, day in enumerate(weekly):
            date_item = QTableWidgetItem(day["date"])
            date_item.setFont(QFont(FONT_MONO, 9))
            self._table.setItem(row, 0, date_item)

            self._table.setItem(row, 1, self._colored(str(day["focus"]),     _STATUS_COLS["FOCUS"]))
            self._table.setItem(row, 2, self._colored(str(day["relax"]),     _STATUS_COLS["RELAX"]))
            self._table.setItem(row, 3, self._colored(str(day["deviation"]), _STATUS_COLS["DEVIATION"]))

            rate_item = QTableWidgetItem(f"{day['focus_rate']}%")
            rate_item.setFont(QFont(FONT_MONO, 9, QFont.Weight.Bold))
            rate = day["focus_rate"]
            if rate >= 70:
                rate_item.setForeground(QColor(_STATUS_COLS["FOCUS"]))
            elif rate >= 40:
                rate_item.setForeground(QColor(_STATUS_COLS["RELAX"]))
            else:
                rate_item.setForeground(QColor(_STATUS_COLS["DEVIATION"]))
            self._table.setItem(row, 4, rate_item)

        logger.info("리포트 갱신 완료")

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_style()
        self.refresh()

    @staticmethod
    def _colored(text: str, color: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setForeground(QColor(color))
        item.setFont(QFont(FONT_MONO, 9))
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        return item
