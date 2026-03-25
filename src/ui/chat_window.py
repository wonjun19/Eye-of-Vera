from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush, QPen, QScreen

from config.settings import OVERLAY_OPACITY, OVERLAY_FADE_SECONDS
from src.core.analyzer import AnalysisResult
from src.utils.logger import get_logger

logger = get_logger(__name__)

# 상태별 테마 색상 (배경, 테두리)
STATUS_COLORS = {
    "FOCUS":     ("#1a2e1a", "#4caf50"),
    "RELAX":     ("#1a1a2e", "#5c6bc0"),
    "DEVIATION": ("#2e1a1a", "#f44336"),
    "UNKNOWN":   ("#2e2e2e", "#9e9e9e"),
}

WINDOW_WIDTH = 380
WINDOW_HEIGHT = 130


class ChatWindow(QWidget):
    """베라의 오버레이 대화창. Always-on-top, 반투명, 드래그 이동 가능."""

    closed_by_user = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._drag_pos = None
        self._border_color = "#9e9e9e"
        self._bg_color = "#2e2e2e"
        self._init_ui()
        self._fade_timer = QTimer(self)
        self._fade_timer.setSingleShot(True)
        self._fade_timer.timeout.connect(self._start_fade_out)

    # ── UI 초기화 ──

    def _init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self._move_to_default()

        # 레이아웃
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)

        # 상단: 이름 + 상태
        header = QHBoxLayout()
        self._name_label = QLabel("VERA")
        self._name_label.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        self._name_label.setStyleSheet("color: #e0e0e0;")
        header.addWidget(self._name_label)

        self._status_label = QLabel("")
        self._status_label.setFont(QFont("Consolas", 9))
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        header.addWidget(self._status_label)
        root.addLayout(header)

        # 메시지
        self._msg_label = QLabel("")
        self._msg_label.setFont(QFont("맑은 고딕", 10))
        self._msg_label.setStyleSheet("color: #f0f0f0;")
        self._msg_label.setWordWrap(True)
        self._msg_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        root.addWidget(self._msg_label, stretch=1)

        # 확인 버튼 (DEVIATION일 때만 표시)
        self._ack_btn = QPushButton("확인")
        self._ack_btn.setFont(QFont("맑은 고딕", 9))
        self._ack_btn.setFixedWidth(70)
        self._ack_btn.setStyleSheet(
            "QPushButton { background: #f44336; color: white; border: none; padding: 4px; }"
            "QPushButton:hover { background: #d32f2f; }"
        )
        self._ack_btn.clicked.connect(self._on_ack)
        self._ack_btn.hide()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self._ack_btn)
        root.addLayout(btn_layout)

    def _move_to_default(self):
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.right() - WINDOW_WIDTH - 20
            y = geo.bottom() - WINDOW_HEIGHT - 20
            self.move(x, y)

    # ── 외부 인터페이스 ──

    def show_result(self, result: AnalysisResult):
        """분석 결과를 대화창에 표시한다."""
        self._bg_color, self._border_color = STATUS_COLORS.get(
            result.status, STATUS_COLORS["UNKNOWN"]
        )
        self._status_label.setText(f"[{result.status}]")
        self._status_label.setStyleSheet(f"color: {self._border_color};")
        self._msg_label.setText(result.message)

        # DEVIATION이면 확인 버튼 표시, 아니면 자동 fade-out
        if result.action_required or result.status == "DEVIATION":
            self._ack_btn.show()
            self._fade_timer.stop()
        else:
            self._ack_btn.hide()
            self._fade_timer.start(OVERLAY_FADE_SECONDS * 1000)

        self.setWindowOpacity(OVERLAY_OPACITY)
        self.show()
        self.raise_()
        logger.info("대화창 표시: %s", result.status)

    # ── 내부 동작 ──

    def _on_ack(self):
        self._ack_btn.hide()
        self._start_fade_out()
        self.closed_by_user.emit()

    def _start_fade_out(self):
        self._anim = QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(800)
        self._anim.setStartValue(self.windowOpacity())
        self._anim.setEndValue(0.0)
        self._anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._anim.finished.connect(self.hide)
        self._anim.start()

    # ── 드래그 이동 ──

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    # ── 커스텀 페인트 ──

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 배경
        painter.setBrush(QBrush(QColor(self._bg_color)))
        painter.setPen(QPen(QColor(self._border_color), 2))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 10, 10)
        painter.end()
