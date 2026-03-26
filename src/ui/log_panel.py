from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QProgressBar, QPushButton,
    QSpinBox, QComboBox, QDialog, QTextEdit, QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QLinearGradient

from src.core.database import Database
from src.ui.design import FONT_MONO, FONT_UI, STATUS_LABELS, STATUS_COLORS, scrollbar_style
from config.user_config import get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ────────────────────────────────────────────────────────────
# 블록 컴포넌트
# ────────────────────────────────────────────────────────────

class _KpiCard(QWidget):
    """상태별 집계 KPI 카드 블록."""

    def __init__(self, label: str, color: str, bg: str, parent=None):
        super().__init__(parent)
        self._color = color
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(3)

        self._count = QLabel("–")
        self._count.setFont(QFont(FONT_MONO, 22, QFont.Weight.Bold))
        self._count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._count.setStyleSheet(f"color: {color}; background: transparent;")

        self._label = QLabel(label)
        self._label.setFont(QFont(FONT_MONO, 8))
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet(f"color: {color}; background: transparent; letter-spacing: 1px;")

        layout.addWidget(self._count)
        layout.addWidget(self._label)

        self.setStyleSheet(
            f"background: {bg};"
            f" border: 1px solid {color}44;"
            f" border-top: 2px solid {color};"
            f" border-radius: 8px;"
        )
        self.setFixedHeight(78)

    def set_value(self, n: int):
        self._count.setText(str(n))


# ────────────────────────────────────────────────────────────
# 메인 로그 패널
# ────────────────────────────────────────────────────────────

class LogPanel(QWidget):
    """최근 정찰 기록 뷰어 — VERA-OS v2.

    블록 구조:
      ┌─ KPI Row ──────────────────────────────────┐
      │  [집중: N]  [휴식: N]  [이탈: N]           │
      ├─ Focus Rate Bar ───────────────────────────┤
      ├─ Control Row ──────────────────────────────┤
      │  표시 건수  [필터]              [새로고침] │
      ├─ Table Block ──────────────────────────────┤
      │  시각 / 상태 / 감지된 활동 / 베라 메시지   │
      └────────────────────────────────────────────┘
    """

    def __init__(self, db: Database):
        super().__init__()
        self._db = db
        self._cached_logs: list[dict] = []
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Eye of Vera — 정찰 기록")
        self.setMinimumSize(580, 460)
        self.resize(640, 540)
        self._apply_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # ── 제목 ──
        title = QLabel("정찰 기록")
        title.setFont(QFont(FONT_MONO, 13, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # ── KPI Row ──
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(10)
        theme = get_config().get_theme()

        self._kpi_focus = _KpiCard("FOCUS",     "#43a047", "#0c1e10")
        self._kpi_relax = _KpiCard("RELAX",     "#5c6bc0", "#0c1224")
        self._kpi_dev   = _KpiCard("DEVIATION", "#e53935", "#200c0c")

        kpi_row.addWidget(self._kpi_focus)
        kpi_row.addWidget(self._kpi_relax)
        kpi_row.addWidget(self._kpi_dev)
        layout.addLayout(kpi_row)

        # ── 오늘 요약 텍스트 ──
        self._today_label = QLabel()
        self._today_label.setFont(QFont(FONT_UI, 9))
        self._today_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._today_label)

        # ── 집중률 바 ──
        self._focus_bar = QProgressBar()
        self._focus_bar.setTextVisible(True)
        self._focus_bar.setFixedHeight(22)
        self._focus_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #2e2e4e;
                border-radius: 6px;
                background: #12122a;
                text-align: center;
                color: #c8e6c9;
                font-family: Consolas;
                font-size: 9pt;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #2e7d32, stop:1 #43a047);
                border-radius: 5px;
            }
        """)
        layout.addWidget(self._focus_bar)

        # ── 구분선 ──
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2e2e4e;")
        layout.addWidget(sep)

        # ── Control Row ──
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(8)

        ctrl_row.addWidget(QLabel("표시:"))
        self._limit_spin = QSpinBox()
        self._limit_spin.setRange(5, 100)
        self._limit_spin.setValue(20)
        self._limit_spin.setSuffix(" 건")
        ctrl_row.addWidget(self._limit_spin)

        ctrl_row.addSpacing(8)
        ctrl_row.addWidget(QLabel("필터:"))
        self._filter_combo = QComboBox()
        self._filter_combo.addItem("전체",  "ALL")
        self._filter_combo.addItem("집중",  "FOCUS")
        self._filter_combo.addItem("휴식",  "RELAX")
        self._filter_combo.addItem("이탈",  "DEVIATION")
        ctrl_row.addWidget(self._filter_combo)

        ctrl_row.addStretch()

        refresh_btn = QPushButton("새로고침 ↻")
        refresh_btn.setFont(QFont(FONT_MONO, 9))
        refresh_btn.setFixedWidth(110)
        refresh_btn.clicked.connect(self.refresh)
        ctrl_row.addWidget(refresh_btn)
        layout.addLayout(ctrl_row)

        # ── Table Block ──
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
        self._table.setShowGrid(False)
        self._table.setAlternatingRowColors(True)
        self._table.cellDoubleClicked.connect(self._show_detail)
        layout.addWidget(self._table, stretch=1)

        hint = QLabel("※ 행 더블클릭 → 상세 보기")
        hint.setStyleSheet("color: #555; font-size: 9px; font-family: Consolas;")
        layout.addWidget(hint)

    def _apply_style(self):
        theme = get_config().get_theme()
        t = theme
        self.setStyleSheet(
            f"QWidget {{ background: {t['bg']}; color: {t['text']}; }}"
            f"QLabel {{ color: {t['text']}; }}"
            f"QPushButton {{"
            f"  background: {t['border']}; color: white; border: none;"
            f"  border-radius: 5px; padding: 6px 12px; font-weight: bold;"
            f"}}"
            f"QPushButton:hover {{ background: {t.get('accent', t['hover'])}; }}"
            f"QSpinBox, QComboBox {{"
            f"  background: {t['input_bg']}; color: {t['text']};"
            f"  border: 1px solid {t['sub_border']}; border-radius: 5px; padding: 4px 8px;"
            f"}}"
            f"QTableWidget {{"
            f"  background: {t['input_bg']}; alternate-background-color: {t['bg']};"
            f"  gridline-color: {t['sub_border']}; border: 1px solid {t['sub_border']};"
            f"  border-radius: 6px;"
            f"}}"
            f"QHeaderView::section {{"
            f"  background: {t['sub_border']}; color: {t['text']};"
            f"  padding: 7px; border: none; font-family: Consolas; font-size: 9pt;"
            f"}}"
            f"QTableWidget::item {{ padding: 5px; }}"
            f"QTableWidget::item:selected {{"
            f"  background: {t['sub_border']}; color: {t['text']};"
            f"}}"
            + scrollbar_style(t["input_bg"], t["border"])
        )

    def refresh(self):
        """데이터 새로고침."""
        today = self._db.get_daily_summary()

        # KPI 카드 업데이트
        self._kpi_focus.set_value(today["focus"])
        self._kpi_relax.set_value(today["relax"])
        self._kpi_dev.set_value(today["deviation"])

        # 요약 텍스트
        self._today_label.setText(
            f"오늘 총 {today['total']}회 정찰"
        )

        # 집중률 바
        self._focus_bar.setValue(int(today["focus_rate"]))
        self._focus_bar.setFormat(f"오늘 집중률  {today['focus_rate']}%")

        # 로그 조회
        limit  = self._limit_spin.value()
        status_filter = self._filter_combo.currentData()
        logs   = self._db.get_recent_logs(limit)

        if status_filter != "ALL":
            logs = [l for l in logs if l["status"] == status_filter]

        self._cached_logs = logs
        self._table.setRowCount(len(logs))

        for row, log in enumerate(logs):
            ts           = log["timestamp"]
            display_time = ts[5:16].replace("T", " ") if len(ts) >= 16 else ts
            status       = log["status"]
            label        = STATUS_LABELS.get(status, status)
            color        = STATUS_COLORS.get(status, "#888")

            self._table.setItem(row, 0, QTableWidgetItem(display_time))

            status_item = QTableWidgetItem(label)
            status_item.setForeground(QColor(color))
            status_item.setFont(QFont(FONT_MONO, 9, QFont.Weight.Bold))
            self._table.setItem(row, 1, status_item)

            self._table.setItem(row, 2, QTableWidgetItem(log.get("detected_activity", "")))
            self._table.setItem(row, 3, QTableWidgetItem(log.get("message", "")))

        logger.info("정찰 기록 갱신 완료 (%d건)", len(logs))

    def _show_detail(self, row: int, _col: int):
        if row < 0 or row >= len(self._cached_logs):
            return
        log    = self._cached_logs[row]
        status = log["status"]
        ts     = log["timestamp"]
        display_time = ts[:16].replace("T", " ") if len(ts) >= 16 else ts
        color  = STATUS_COLORS.get(status, "#888")
        label  = STATUS_LABELS.get(status, status)

        dlg = QDialog(self)
        dlg.setWindowTitle("정찰 상세 기록")
        dlg.setMinimumSize(460, 340)
        dlg.resize(500, 380)

        theme = get_config().get_theme()
        t = theme
        dlg.setStyleSheet(
            f"QDialog {{ background: {t['bg']}; color: {t['text']}; }}"
            f"QLabel {{ color: {t['text']}; }}"
            f"QTextEdit {{"
            f"  background: {t['input_bg']}; color: {t['text']};"
            f"  border: 1px solid {t['sub_border']}; border-radius: 6px; padding: 8px;"
            f"}}"
            f"QPushButton {{"
            f"  background: {t['border']}; color: white; border: none;"
            f"  border-radius: 5px; padding: 8px 20px; font-weight: bold;"
            f"}}"
            f"QPushButton:hover {{ background: {t.get('accent', t['hover'])}; }}"
        )

        dlayout = QVBoxLayout(dlg)
        dlayout.setContentsMargins(18, 18, 18, 18)
        dlayout.setSpacing(12)

        header = QLabel(f"{display_time}    <span style='color:{color};font-family:Consolas;'>{label}</span>")
        header.setFont(QFont(FONT_UI, 12, QFont.Weight.Bold))
        header.setTextFormat(Qt.TextFormat.RichText)
        dlayout.addWidget(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {color};")
        dlayout.addWidget(sep)

        lbl_act = QLabel("감지된 활동")
        lbl_act.setFont(QFont(FONT_MONO, 9))
        lbl_act.setStyleSheet(f"color: {t['text']}88;")
        dlayout.addWidget(lbl_act)

        activity_text = QTextEdit()
        activity_text.setReadOnly(True)
        activity_text.setPlainText(log.get("detected_activity", ""))
        activity_text.setFont(QFont(FONT_MONO, 9))
        dlayout.addWidget(activity_text, stretch=1)

        lbl_msg = QLabel("베라 메시지")
        lbl_msg.setFont(QFont(FONT_MONO, 9))
        lbl_msg.setStyleSheet(f"color: {t['text']}88;")
        dlayout.addWidget(lbl_msg)

        message_text = QTextEdit()
        message_text.setReadOnly(True)
        message_text.setPlainText(log.get("message", ""))
        message_text.setFont(QFont(FONT_UI, 10))
        dlayout.addWidget(message_text, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("닫기")
        close_btn.setFixedWidth(90)
        close_btn.clicked.connect(dlg.close)
        btn_row.addWidget(close_btn)
        dlayout.addLayout(btn_row)

        dlg.exec()

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_style()
        self.refresh()
