from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QProgressBar,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from src.core.database import Database
from src.utils.logger import get_logger

logger = get_logger(__name__)

STATUS_COLORS = {
    "FOCUS": "#4caf50",
    "RELAX": "#5c6bc0",
    "DEVIATION": "#f44336",
}


class ReportWindow(QWidget):
    """주간 결산 리포트 창."""

    def __init__(self, db: Database):
        super().__init__()
        self._db = db
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Eye of Vera — 주간 결산")
        self.setMinimumSize(520, 420)
        self.setStyleSheet("background: #1e1e2e; color: #e0e0e0;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 제목
        title = QLabel("주간 작전 결산 보고")
        title.setFont(QFont("맑은 고딕", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 오늘 요약
        self._today_label = QLabel()
        self._today_label.setFont(QFont("맑은 고딕", 11))
        self._today_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._today_label)

        # 집중률 바
        self._focus_bar = QProgressBar()
        self._focus_bar.setTextVisible(True)
        self._focus_bar.setFixedHeight(28)
        self._focus_bar.setStyleSheet("""
            QProgressBar { border: 1px solid #444; border-radius: 6px; background: #2e2e3e; text-align: center; color: white; }
            QProgressBar::chunk { background: #4caf50; border-radius: 5px; }
        """)
        layout.addWidget(self._focus_bar)

        # 주간 테이블
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["날짜", "FOCUS", "RELAX", "DEVIATION", "집중률"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._table.setStyleSheet("""
            QTableWidget { background: #2e2e3e; gridline-color: #444; border: none; }
            QHeaderView::section { background: #3e3e4e; color: #e0e0e0; padding: 6px; border: none; }
            QTableWidget::item { padding: 4px; }
        """)
        layout.addWidget(self._table)

    def refresh(self):
        """데이터를 새로고침하여 표시."""
        # 오늘 요약
        today = self._db.get_daily_summary()
        self._today_label.setText(
            f"오늘 총 {today['total']}회 정찰  |  "
            f"집중 {today['focus']}  휴식 {today['relax']}  이탈 {today['deviation']}"
        )
        self._focus_bar.setValue(int(today["focus_rate"]))
        self._focus_bar.setFormat(f"오늘 집중률: {today['focus_rate']}%")

        # 주간 테이블
        weekly = self._db.get_weekly_summary()
        self._table.setRowCount(len(weekly))

        for row, day in enumerate(weekly):
            self._table.setItem(row, 0, QTableWidgetItem(day["date"]))
            self._table.setItem(row, 1, self._colored_item(str(day["focus"]), "#4caf50"))
            self._table.setItem(row, 2, self._colored_item(str(day["relax"]), "#5c6bc0"))
            self._table.setItem(row, 3, self._colored_item(str(day["deviation"]), "#f44336"))
            self._table.setItem(row, 4, QTableWidgetItem(f"{day['focus_rate']}%"))

        logger.info("리포트 갱신 완료")

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh()

    @staticmethod
    def _colored_item(text: str, color: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setForeground(QColor(color))
        return item
