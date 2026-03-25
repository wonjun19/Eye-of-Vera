import os
import sys

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication, QInputDialog
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QAction
from src.utils.logger import get_logger

logger = get_logger(__name__)

# 아이콘 경로 (PyInstaller 빌드 / 개발 환경 모두 지원)
_ICON_DIR = os.path.join(
    getattr(sys, '_MEIPASS', os.path.abspath('.')),
    'assets', 'icons',
)


def _load_icon() -> QIcon:
    """아이콘 파일을 로드한다. 없으면 기본 아이콘을 생성한다."""
    for name in ('Eye_Of_Vera.ico', 'Eye_Of_Vera.png'):
        path = os.path.join(_ICON_DIR, name)
        if os.path.isfile(path):
            return QIcon(path)

    # fallback: 기본 원형 아이콘
    px = QPixmap(64, 64)
    px.fill(QColor(0, 0, 0, 0))
    painter = QPainter(px)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor("#5c6bc0"))
    painter.setPen(QColor("#ffffff"))
    painter.drawEllipse(4, 4, 56, 56)
    painter.setPen(QColor("#ffffff"))
    font = painter.font()
    font.setPixelSize(28)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(px.rect(), 0x0084, "V")  # AlignCenter
    painter.end()
    return QIcon(px)


class TrayMenu:
    """시스템 트레이 아이콘 + 메뉴 관리."""

    def __init__(self, app: QApplication, on_mission_change=None,
                 on_pause_resume=None, on_report=None, on_chat=None,
                 on_settings=None, on_logs=None, on_quit=None,
                 on_free_mode_toggle=None):
        self._app = app
        self._on_mission_change = on_mission_change
        self._on_pause_resume = on_pause_resume
        self._on_report = on_report
        self._on_chat = on_chat
        self._on_settings = on_settings
        self._on_logs = on_logs
        self._on_quit = on_quit
        self._on_free_mode_toggle = on_free_mode_toggle
        self._paused = False
        self._free_mode = False

        self._tray = QSystemTrayIcon(_load_icon(), parent=None)
        self._tray.setToolTip("Eye of Vera")
        self._build_menu()
        self._tray.show()

    def _build_menu(self):
        menu = QMenu()

        # 작전 변경
        mission_action = QAction("작전 변경", menu)
        mission_action.triggered.connect(self._change_mission)
        menu.addAction(mission_action)

        # 베라와 대화
        chat_action = QAction("베라와 대화", menu)
        chat_action.triggered.connect(self._open_chat)
        menu.addAction(chat_action)

        # 정찰 기록
        logs_action = QAction("정찰 기록", menu)
        logs_action.triggered.connect(self._open_logs)
        menu.addAction(logs_action)

        # 주간 결산
        report_action = QAction("주간 결산", menu)
        report_action.triggered.connect(self._open_report)
        menu.addAction(report_action)

        # 설정
        settings_action = QAction("설정", menu)
        settings_action.triggered.connect(self._open_settings)
        menu.addAction(settings_action)

        menu.addSeparator()

        # 자유 상호작용 모드
        self._free_mode_action = QAction("자유 상호작용 모드", menu)
        self._free_mode_action.triggered.connect(self._toggle_free_mode)
        menu.addAction(self._free_mode_action)

        # 일시 정지 / 재개
        self._pause_action = QAction("일시 정지", menu)
        self._pause_action.triggered.connect(self._toggle_pause)
        menu.addAction(self._pause_action)

        menu.addSeparator()

        # 종료
        quit_action = QAction("작전 종료", menu)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)

        self._tray.setContextMenu(menu)

    def _change_mission(self):
        text, ok = QInputDialog.getText(
            None, "Eye of Vera", "새로운 작전 목표를 입력하십시오:"
        )
        if ok and text.strip():
            logger.info("작전 목표 변경: %s", text.strip())
            if self._on_mission_change:
                self._on_mission_change(text.strip())

    def _toggle_pause(self):
        self._paused = not self._paused
        if self._paused:
            self._pause_action.setText("작전 재개")
            logger.info("스케줄러 일시 정지")
        else:
            self._pause_action.setText("일시 정지")
            logger.info("스케줄러 재개")
        if self._on_pause_resume:
            self._on_pause_resume(self._paused)

    def _toggle_free_mode(self):
        self._free_mode = not self._free_mode
        if self._free_mode:
            self._free_mode_action.setText("정찰 모드로 복귀")
            self._pause_action.setEnabled(False)
            logger.info("자유 상호작용 모드 활성화")
        else:
            self._free_mode_action.setText("자유 상호작용 모드")
            self._pause_action.setEnabled(True)
            logger.info("자유 상호작용 모드 비활성화")
        if self._on_free_mode_toggle:
            self._on_free_mode_toggle(self._free_mode)

    def _open_chat(self):
        logger.info("채팅 패널 열기")
        if self._on_chat:
            self._on_chat()

    def _open_logs(self):
        logger.info("정찰 기록 열기")
        if self._on_logs:
            self._on_logs()

    def _open_settings(self):
        logger.info("설정 패널 열기")
        if self._on_settings:
            self._on_settings()

    def _open_report(self):
        logger.info("주간 결산 열기")
        if self._on_report:
            self._on_report()

    def _quit(self):
        logger.info("앱 종료 요청")
        if self._on_quit:
            self._on_quit()
        self._tray.hide()
        self._app.quit()

    def show_notification(self, title: str, message: str):
        self._tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 3000)
