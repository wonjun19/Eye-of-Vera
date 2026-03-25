from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLineEdit, QPushButton, QLabel, QScrollArea, QFrame, QSlider,
    QComboBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QRect, QPoint
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush, QPen, QKeyEvent, QCursor

from src.core.analyzer import Analyzer
from src.core.database import Database
from src.core.knowledge import find_relevant_knowledge
from config.user_config import get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)

# 선택 가능한 Gemini 모델
GEMINI_MODELS = [
    ("gemini-3.1-flash-lite-preview", "Flash Lite"),
    ("gemini-3-flash-preview", "Flash"),
    ("gemini-2.5-flash", "2.5 Flash"),
    ("gemini-3.1-pro-preview", "Pro"),
]

# 크기 상수
MIN_WIDTH, MIN_HEIGHT = 320, 400
MAX_WIDTH, MAX_HEIGHT = 800, 900
DEFAULT_WIDTH, DEFAULT_HEIGHT = 420, 560
RESIZE_MARGIN = 8


class _ChatInput(QTextEdit):
    """Enter로 전송, Shift+Enter로 줄바꿈하는 입력 위젯."""
    submitted = pyqtSignal()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                super().keyPressEvent(event)
            else:
                self.submitted.emit()
            return
        super().keyPressEvent(event)


class _ChatWorker(QThread):
    """백그라운드에서 Gemini API를 호출하는 워커 스레드."""
    finished = pyqtSignal(str)

    def __init__(self, analyzer: Analyzer, message: str,
                 history: list[dict], context: str = "",
                 knowledge: str = "", screen_context: str = ""):
        super().__init__()
        self._analyzer = analyzer
        self._message = message
        self._history = history
        self._context = context
        self._knowledge = knowledge
        self._screen_context = screen_context

    def run(self):
        reply = self._analyzer.chat(
            self._message, self._history,
            self._context, self._knowledge,
            self._screen_context,
        )
        self.finished.emit(reply)


class ChatPanel(QWidget):
    """베라와 양방향 소통이 가능한 채팅 패널."""

    def __init__(self, analyzer: Analyzer, db: Database):
        super().__init__()
        self._analyzer = analyzer
        self._db = db
        self._history: list[dict] = []
        self._screen_context: str = ""
        self._worker: _ChatWorker | None = None
        self._bg_opacity: float = 0.95
        self._bubbles: list[tuple[QLabel, bool]] = []  # (widget, is_user)
        self._resizing = False
        self._resize_edge = None
        self._resize_origin = None
        self._resize_geo = None
        # 테마 색상 캐시
        self._theme = get_config().get_theme()
        self._init_ui()

    # ── 테마 ──

    def _load_theme(self):
        cfg = get_config()
        self._theme = cfg.get_theme()
        self._bg_opacity = cfg.get("appearance", "default_opacity") / 100.0
        self._base_font = cfg.get("appearance", "base_font_size")

    def _apply_theme(self):
        """현재 테마를 모든 위젯에 적용한다."""
        t = self._theme

        self._title.setStyleSheet(f"color: {t['border']};")
        self._opacity_icon.setStyleSheet(f"color: {t['text']};")
        self._close_btn.setStyleSheet(
            f"QPushButton {{ color: {t['text']}; background: transparent; border: none; }}"
            f"QPushButton:hover {{ color: #f44336; }}"
        )
        self._line.setStyleSheet(f"color: {t['border']};")
        self._scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
            f"QScrollBar:vertical {{ background: {t['input_bg']}; width: 6px; }}"
            f"QScrollBar::handle:vertical {{ background: {t['border']}; border-radius: 3px; }}"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
        )
        self._input.setStyleSheet(
            f"QTextEdit {{"
            f"  background: {t['input_bg']}; color: {t['text']}; border: 1px solid {t['sub_border']};"
            f"  border-radius: 6px; padding: 6px 10px;"
            f"}}"
            f"QTextEdit:focus {{ border-color: {t['border']}; }}"
        )
        self._model_combo.setStyleSheet(
            f"QComboBox {{"
            f"  background: {t['input_bg']}; color: {t['text']}; border: 1px solid {t['sub_border']};"
            f"  border-radius: 4px; padding: 2px 6px; font-size: 11px;"
            f"}}"
            f"QComboBox:hover {{ border-color: {t['border']}; }}"
            f"QComboBox::drop-down {{ border: none; }}"
            f"QComboBox::down-arrow {{ image: none; }}"
            f"QComboBox QAbstractItemView {{"
            f"  background: {t['input_bg']}; color: {t['text']}; border: 1px solid {t['border']};"
            f"  selection-background-color: {t['sub_border']};"
            f"}}"
        )
        self._send_btn.setStyleSheet(
            f"QPushButton {{ background: {t['border']}; color: white; border: none; border-radius: 6px; }}"
            f"QPushButton:hover {{ background: {t['hover']}; }}"
            f"QPushButton:disabled {{ background: {t['sub_border']}; color: #666; }}"
        )
        self._opacity_slider.setStyleSheet(
            f"QSlider::groove:horizontal {{ background: {t['sub_border']}; height: 4px; border-radius: 2px; }}"
            f"QSlider::handle:horizontal {{ background: {t['border']}; width: 12px; height: 12px; margin: -4px 0; border-radius: 6px; }}"
            f"QSlider::handle:horizontal:hover {{ background: {t['hover']}; }}"
        )
        self._grip_label.setStyleSheet(f"color: {t['border']}; background: transparent; font-size: 12px;")

        # 기존 버블 재스타일링
        for bubble, is_user in self._bubbles:
            self._style_bubble(bubble, is_user)

        self.update()  # paintEvent 갱신

    def _style_bubble(self, bubble: QLabel, is_user: bool):
        t = self._theme
        if is_user:
            bubble.setStyleSheet(
                f"background: {t['user_bubble']}; color: {t['text']}; "
                f"border-radius: 10px; padding: 8px 12px;"
                f"border: 1px solid {t['sub_border']};"
            )
        else:
            bubble.setStyleSheet(
                f"background: {t['vera_bubble']}; color: {t['vera_text']}; "
                f"border-radius: 10px; padding: 8px 12px;"
                f"border: 1px solid {t['sub_border']};"
            )

    # ── UI 초기화 ──

    def _init_ui(self):
        self.setWindowTitle("VERA — 통신 채널")
        self.setMinimumSize(MIN_WIDTH, MIN_HEIGHT)
        self.setMaximumSize(MAX_WIDTH, MAX_HEIGHT)
        self.resize(DEFAULT_WIDTH, DEFAULT_HEIGHT)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self._drag_pos = None
        self._move_to_default()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self._container.setMouseTracking(True)
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.setContentsMargins(14, 10, 14, 14)
        self._container_layout.setSpacing(8)

        # ── 헤더 ──
        header = QHBoxLayout()
        self._title = QLabel("VERA — 통신 채널")
        self._title.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        header.addWidget(self._title)
        header.addStretch()

        self._model_combo = QComboBox()
        self._model_combo.setFixedWidth(100)
        self._model_combo.setToolTip("AI 모델 선택")
        for model_id, display in GEMINI_MODELS:
            self._model_combo.addItem(display, model_id)
        self._model_combo.currentIndexChanged.connect(self._on_model_changed)
        header.addWidget(self._model_combo)

        self._opacity_icon = QLabel("◐")
        self._opacity_icon.setFont(QFont("Consolas", 10))
        header.addWidget(self._opacity_icon)

        self._opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._opacity_slider.setRange(30, 100)
        self._opacity_slider.setValue(int(self._bg_opacity * 100))
        self._opacity_slider.setFixedWidth(80)
        self._opacity_slider.setToolTip("창 투명도 조절")
        self._opacity_slider.valueChanged.connect(self._on_opacity_changed)
        header.addWidget(self._opacity_slider)

        self._close_btn = QPushButton("✕")
        self._close_btn.setFixedSize(28, 28)
        self._close_btn.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        self._close_btn.clicked.connect(self.hide)
        header.addWidget(self._close_btn)
        self._container_layout.addLayout(header)

        # ── 구분선 ──
        self._line = QFrame()
        self._line.setFrameShape(QFrame.Shape.HLine)
        self._container_layout.addWidget(self._line)

        # ── 메시지 영역 ──
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._messages_widget = QWidget()
        self._messages_widget.setMouseTracking(True)
        self._messages_layout = QVBoxLayout(self._messages_widget)
        self._messages_layout.setContentsMargins(0, 4, 0, 4)
        self._messages_layout.setSpacing(8)
        self._messages_layout.addStretch()

        self._scroll.setWidget(self._messages_widget)
        self._container_layout.addWidget(self._scroll, stretch=1)

        # ── 입력 영역 ──
        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self._input = _ChatInput()
        self._input.setPlaceholderText("메시지를 입력하십시오... (Shift+Enter: 줄바꿈)")
        self._input.setFont(QFont("맑은 고딕", 10))
        self._input.setFixedHeight(36)
        self._input.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self._input.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._input.submitted.connect(self._send_message)
        self._input.textChanged.connect(self._adjust_input_height)
        input_row.addWidget(self._input, stretch=1)

        self._send_btn = QPushButton("전송")
        self._send_btn.setFont(QFont("맑은 고딕", 9, QFont.Weight.Bold))
        self._send_btn.setFixedSize(56, 36)
        self._send_btn.clicked.connect(self._send_message)
        input_row.addWidget(self._send_btn)

        self._container_layout.addLayout(input_row)

        # ── 리사이즈 그립 ──
        self._grip_label = QLabel("⠿")
        self._grip_label.setFixedSize(16, 16)
        self._grip_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        grip_row = QHBoxLayout()
        grip_row.addStretch()
        grip_row.addWidget(self._grip_label)
        grip_row.setContentsMargins(0, 0, 2, 0)
        self._container_layout.addLayout(grip_row)

        root.addWidget(self._container)

        # 초기 테마 적용
        self._apply_theme()

        # 초기 인사 메시지
        self._add_vera_message("지휘관, 통신 채널을 개설했습니다. 무엇이든 말씀하십시오.")

    def _move_to_default(self):
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.right() - self.width() - 20
            y = geo.bottom() - self.height() - 160
            self.move(x, y)

    # ── 반응형 폰트 계산 ──

    def _scaled_font_size(self, base: int) -> int:
        w = self.width()
        scale = 0.85 + (w - MIN_WIDTH) / (MAX_WIDTH - MIN_WIDTH) * 0.5
        return max(base - 1, round(base * scale))

    def _update_responsive_fonts(self):
        base = getattr(self, '_base_font', 10)
        title_size = self._scaled_font_size(base + 1)
        bubble_size = self._scaled_font_size(base)
        input_size = self._scaled_font_size(base)
        btn_size = self._scaled_font_size(base - 1)

        self._title.setFont(QFont("Consolas", title_size, QFont.Weight.Bold))
        for bubble, _ in self._bubbles:
            bubble.setFont(QFont("맑은 고딕", bubble_size))
        self._input.setFont(QFont("맑은 고딕", input_size))
        self._send_btn.setFont(QFont("맑은 고딕", btn_size, QFont.Weight.Bold))

        btn_w = max(48, round(56 * self.width() / DEFAULT_WIDTH))
        btn_h = max(30, round(36 * self.height() / DEFAULT_HEIGHT))
        self._send_btn.setFixedSize(btn_w, btn_h)

    # ── 메시지 추가 ──

    def _add_bubble(self, text: str, is_user: bool):
        base = getattr(self, '_base_font', 10)
        bubble_size = self._scaled_font_size(base)
        bubble = QLabel(text)
        bubble.setWordWrap(True)
        bubble.setFont(QFont("맑은 고딕", bubble_size))
        bubble.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        bubble.setAlignment(
            Qt.AlignmentFlag.AlignRight if is_user
            else Qt.AlignmentFlag.AlignLeft
        )
        self._style_bubble(bubble, is_user)
        self._bubbles.append((bubble, is_user))

        count = self._messages_layout.count()
        self._messages_layout.insertWidget(count - 1, bubble)
        QTimer.singleShot(50, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        vbar = self._scroll.verticalScrollBar()
        vbar.setValue(vbar.maximum())

    def receive_vera_comment(self, text: str, screen_description: str = ""):
        """외부(스케줄러 등)에서 베라의 코멘트를 채팅에 추가한다."""
        if screen_description:
            self._screen_context = screen_description
        self._add_vera_message(text)
        # 채팅 패널이 닫혀 있으면 자동으로 열기
        if not self.isVisible():
            self.show()
            self.raise_()

    def _add_user_message(self, text: str):
        self._add_bubble(text, is_user=True)
        self._history.append({"role": "user", "text": text})

    def _add_vera_message(self, text: str):
        self._add_bubble(text, is_user=False)
        self._history.append({"role": "vera", "text": text})

    # ── 전송 로직 ──

    def _send_message(self):
        text = self._input.toPlainText().strip()
        if not text:
            return

        self._add_user_message(text)
        self._input.clear()
        self._input.setFixedHeight(36)
        self._set_loading(True)

        history_for_api = self._history[:-1]
        context = self._db.build_chat_context()

        # 지식 파일 검색
        cfg = get_config()
        enabled_files = cfg.get("knowledge", "enabled_files") or []
        knowledge = find_relevant_knowledge(text, enabled_files)

        self._worker = _ChatWorker(
            self._analyzer, text, history_for_api, context, knowledge,
            self._screen_context,
        )
        self._worker.finished.connect(self._on_reply)
        self._worker.start()

    def _on_reply(self, reply: str):
        self._set_loading(False)
        self._add_vera_message(reply)
        self._worker = None

    def _set_loading(self, loading: bool):
        self._send_btn.setEnabled(not loading)
        self._input.setReadOnly(loading)
        if loading:
            self._input.setPlaceholderText("베라 응답 대기 중...")
        else:
            self._input.setPlaceholderText("메시지를 입력하십시오... (Shift+Enter: 줄바꿈)")
            self._input.setFocus()

    # ── 모델 변경 ──

    def _on_model_changed(self, index: int):
        model_id = self._model_combo.currentData()
        if model_id:
            get_config().set("ai", "model", model_id)
            get_config().save()
            logger.info("AI 모델 변경: %s", model_id)

    # ── 입력 높이 자동 조절 ──

    def _adjust_input_height(self):
        doc_height = int(self._input.document().size().height())
        new_height = max(36, min(120, doc_height + 14))
        self._input.setFixedHeight(new_height)

    # ── 투명도 조절 ──

    def _on_opacity_changed(self, value: int):
        self._bg_opacity = value / 100.0
        self.update()

    # ── 리사이즈 가장자리 감지 ──

    def _edge_at(self, pos: QPoint) -> str | None:
        r = self.rect()
        m = RESIZE_MARGIN
        edges = ""
        if pos.y() <= m:
            edges += "t"
        elif pos.y() >= r.height() - m:
            edges += "b"
        if pos.x() <= m:
            edges += "l"
        elif pos.x() >= r.width() - m:
            edges += "r"
        return edges if edges else None

    def _cursor_for_edge(self, edge: str | None) -> Qt.CursorShape:
        mapping = {
            "t": Qt.CursorShape.SizeVerCursor,
            "b": Qt.CursorShape.SizeVerCursor,
            "l": Qt.CursorShape.SizeHorCursor,
            "r": Qt.CursorShape.SizeHorCursor,
            "tl": Qt.CursorShape.SizeFDiagCursor,
            "br": Qt.CursorShape.SizeFDiagCursor,
            "tr": Qt.CursorShape.SizeBDiagCursor,
            "bl": Qt.CursorShape.SizeBDiagCursor,
        }
        return mapping.get(edge, Qt.CursorShape.ArrowCursor)

    # ── 드래그 이동 + 리사이즈 ──

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        edge = self._edge_at(event.pos())
        if edge:
            self._resizing = True
            self._resize_edge = edge
            self._resize_origin = event.globalPosition().toPoint()
            self._resize_geo = self.geometry()
        else:
            self._drag_pos = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        if self._resizing and self._resize_edge:
            self._do_resize(event.globalPosition().toPoint())
            return
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            return
        edge = self._edge_at(event.pos())
        self.setCursor(self._cursor_for_edge(edge))

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        if self._resizing:
            self._resizing = False
            self._resize_edge = None
            self._resize_origin = None
            self._resize_geo = None

    def _do_resize(self, global_pos: QPoint):
        dx = global_pos.x() - self._resize_origin.x()
        dy = global_pos.y() - self._resize_origin.y()
        geo = QRect(self._resize_geo)
        edge = self._resize_edge

        if "r" in edge:
            geo.setRight(geo.right() + dx)
        if "b" in edge:
            geo.setBottom(geo.bottom() + dy)
        if "l" in edge:
            geo.setLeft(geo.left() + dx)
        if "t" in edge:
            geo.setTop(geo.top() + dy)

        w = max(MIN_WIDTH, min(MAX_WIDTH, geo.width()))
        h = max(MIN_HEIGHT, min(MAX_HEIGHT, geo.height()))

        if "l" in edge:
            geo.setLeft(geo.right() - w)
        if "t" in edge:
            geo.setTop(geo.bottom() - h)

        geo.setWidth(w)
        geo.setHeight(h)
        self.setGeometry(geo)

    # ── 이벤트 ──

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_responsive_fonts()

    def showEvent(self, event):
        """열릴 때마다 최신 테마·모델 설정을 적용한다."""
        super().showEvent(event)
        self._load_theme()
        self._opacity_slider.setValue(int(self._bg_opacity * 100))
        # 모델 콤보 동기화
        current_model = get_config().get("ai", "model")
        idx = self._model_combo.findData(current_model)
        if idx >= 0:
            self._model_combo.blockSignals(True)
            self._model_combo.setCurrentIndex(idx)
            self._model_combo.blockSignals(False)
        self._apply_theme()
        self._update_responsive_fonts()

    # ── 커스텀 페인트 ──

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        bg = QColor(self._theme["bg"])
        bg.setAlphaF(self._bg_opacity)
        border = QColor(self._theme["border"])
        border.setAlphaF(min(1.0, self._bg_opacity + 0.1))
        painter.setBrush(QBrush(bg))
        painter.setPen(QPen(border, 2))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 12, 12)
        painter.end()
