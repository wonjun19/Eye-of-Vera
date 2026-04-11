from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush, QPen, QLinearGradient

from config.settings import OVERLAY_OPACITY, OVERLAY_FADE_SECONDS
from src.core.analyzer import AnalysisResult
from src.ui.design import (
    STATUS, FONT_MONO, FONT_UI, PULSE_INTERVAL, DURATION_SLOW, RADIUS_MD,
    draw_corner_brackets, draw_scanlines,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

WINDOW_WIDTH  = 440
WINDOW_HEIGHT = 186


class ChatWindow(QWidget):
    """베라의 오버레이 알림창 — VERA-OS v2.

    블록 구조:
      ┌─ Header Block ─────────────────────┐
      │  VERA  ◉  [집중]                   │
      ├─ Separator ────────────────────────┤
      │  Message Block                     │
      ├─ Action Block (DEVIATION 전용) ────┤
      │                          [확인 ✓] │
      └────────────────────────────────────┘
    """

    closed_by_user = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._drag_pos    = None
        self._status_meta = STATUS["UNKNOWN"]
        self._pulse_alpha = 0.0
        self._pulse_dir   = 1
        self._init_ui()

        self._fade_timer = QTimer(self)
        self._fade_timer.setSingleShot(True)
        self._fade_timer.timeout.connect(self._start_fade_out)

        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(PULSE_INTERVAL)
        self._pulse_timer.timeout.connect(self._tick_pulse)

    # ────────────────────────────────────
    # UI 초기화
    # ────────────────────────────────────

    def _init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self._move_to_default()

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 12)
        root.setSpacing(6)

        # ── Header Block ──
        header = QHBoxLayout()
        header.setSpacing(8)

        self._vera_label = QLabel("▎ VERA")
        self._vera_label.setFont(QFont(FONT_MONO, 10, QFont.Weight.Bold))
        self._vera_label.setStyleSheet(
            "color: #7986cb; letter-spacing: 4px; background: transparent;"
        )
        header.addWidget(self._vera_label)

        self._status_icon = QLabel("○")
        self._status_icon.setFont(QFont(FONT_MONO, 13))
        self._status_icon.setStyleSheet("color: #616161; background: transparent;")
        header.addWidget(self._status_icon)

        header.addStretch()

        self._status_badge = QLabel("  –  ")
        self._status_badge.setFont(QFont(FONT_MONO, 8, QFont.Weight.Bold))
        self._status_badge.setStyleSheet(
            "color: #9e9e9e; background: #252540;"
            " border: 1px solid #3a3a5e; border-radius: 4px;"
            " padding: 3px 10px; letter-spacing: 2px;"
        )
        header.addWidget(self._status_badge)
        root.addLayout(header)

        # ── Separator Block ──
        self._sep = QLabel()
        self._sep.setFixedHeight(1)
        self._sep.setStyleSheet("background: #3a3a5e;")
        root.addWidget(self._sep)
        root.addSpacing(2)

        # ── Message Block ──
        self._msg_label = QLabel("")
        self._msg_label.setFont(QFont(FONT_UI, 10))
        self._msg_label.setStyleSheet("color: #e0e0f0; background: transparent;")
        self._msg_label.setWordWrap(True)
        self._msg_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        root.addWidget(self._msg_label, stretch=1)

        # ── Action Block ──
        self._ack_btn = QPushButton("확인  ✓")
        self._ack_btn.setFont(QFont(FONT_MONO, 9, QFont.Weight.Bold))
        self._ack_btn.setFixedWidth(92)
        self._ack_btn.setStyleSheet(
            "QPushButton {"
            "  background: #b71c1c; color: #ffcdd2;"
            "  border: 1px solid #ef5350; border-radius: 6px;"
            "  padding: 6px 10px; letter-spacing: 1px;"
            "}"
            "QPushButton:hover { background: #d32f2f; color: white; border-color: #ff5252; }"
        )
        self._ack_btn.clicked.connect(self._on_ack)
        self._ack_btn.hide()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(self._ack_btn)
        root.addLayout(btn_row)

    def _move_to_default(self):
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(geo.right() - WINDOW_WIDTH - 20, geo.bottom() - WINDOW_HEIGHT - 20)

    # ────────────────────────────────────
    # 외부 인터페이스
    # ────────────────────────────────────

    def show_result(self, result: AnalysisResult):
        """분석 결과를 오버레이에 표시한다."""
        self._status_meta = STATUS.get(result.status, STATUS["UNKNOWN"])
        meta = self._status_meta

        # Header 업데이트
        self._status_icon.setText(meta["icon"])
        self._status_icon.setStyleSheet(f"color: {meta['border']}; background: transparent;")

        self._status_badge.setText(f"  {meta['label']}  ")
        self._status_badge.setStyleSheet(
            f"color: {meta['text']}; background: {meta['badge_bg']};"
            f" border: 1px solid {meta['border']}; border-radius: 4px;"
            f" padding: 3px 10px; font-weight: bold; font-size: 8pt; letter-spacing: 2px;"
        )
        self._sep.setStyleSheet(f"background: {meta['border']};")

        # Message 업데이트
        self._msg_label.setText(result.message)
        self._msg_label.setStyleSheet(f"color: {meta['text']}; background: transparent;")

        # Action 로직
        if result.action_required or result.status == "DEVIATION":
            self._ack_btn.show()
            self._fade_timer.stop()
            self._pulse_alpha = 0.15
            self._pulse_dir   = 1
            self._pulse_timer.start()
        else:
            self._ack_btn.hide()
            self._pulse_timer.stop()
            self._pulse_alpha = 0.0
            self._fade_timer.start(OVERLAY_FADE_SECONDS * 1000)

        self.setWindowOpacity(OVERLAY_OPACITY)
        self.show()
        self.raise_()
        logger.info("오버레이 표시: %s", result.status)

    # ────────────────────────────────────
    # 내부 동작
    # ────────────────────────────────────

    def _tick_pulse(self):
        self._pulse_alpha += self._pulse_dir * 0.035
        if self._pulse_alpha >= 1.0:
            self._pulse_alpha = 1.0; self._pulse_dir = -1
        elif self._pulse_alpha <= 0.15:
            self._pulse_alpha = 0.15; self._pulse_dir = 1
        self.update()

    def _on_ack(self):
        self._pulse_timer.stop()
        self._pulse_alpha = 0.0
        self._ack_btn.hide()
        self._start_fade_out()
        self.closed_by_user.emit()

    def _start_fade_out(self):
        self._anim = QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(DURATION_SLOW)
        self._anim.setStartValue(self.windowOpacity())
        self._anim.setEndValue(0.0)
        self._anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._anim.finished.connect(self.hide)
        self._anim.start()

    # ────────────────────────────────────
    # 드래그 이동
    # ────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    # ────────────────────────────────────
    # 커스텀 렌더링
    # ────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        meta = self._status_meta
        rect = self.rect().adjusted(1, 1, -1, -1)

        # 그라디언트 배경 (좌상 → 우하, 3단계 깊이)
        grad = QLinearGradient(0, 0, rect.width(), rect.height())
        grad.setColorAt(0.0, QColor(meta["bg"]))
        grad.setColorAt(0.5, QColor(meta["bg2"]))
        grad.setColorAt(1.0, QColor(meta["bg"]).darker(120))
        painter.setBrush(QBrush(grad))

        # 테두리 (DEVIATION 맥동 효과)
        border = QColor(meta["border"])
        if self._pulse_alpha > 0.0:
            border.setAlphaF(0.35 + self._pulse_alpha * 0.65)
        painter.setPen(QPen(border, 1.5))

        painter.drawRoundedRect(rect, RADIUS_MD, RADIUS_MD)

        # 상태 악센트 상단 바
        accent = QColor(meta["accent"])
        accent.setAlphaF(0.7)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(accent))
        painter.drawRoundedRect(
            rect.left() + 8, rect.top() + 2,
            rect.width() - 16, 2,
            1, 1,
        )

        # 스캔라인 오버레이
        draw_scanlines(painter, rect)

        # 코너 브라켓
        draw_corner_brackets(painter, rect, meta["accent"], size=16, width=1.2)

        painter.end()
