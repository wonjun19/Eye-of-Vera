import os
import sys
from PyQt6.QtWidgets import QApplication, QInputDialog
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QObject, pyqtSignal

from src.core.analyzer import Analyzer, AnalysisResult, FreeCommentResult
from src.core.database import Database
from src.core.scheduler import Scheduler
from src.ui.chat_window import ChatWindow
from src.ui.report_window import ReportWindow
from src.ui.chat_panel import ChatPanel
from src.ui.settings_panel import SettingsPanel
from src.ui.log_panel import LogPanel
from src.ui.tray_menu import TrayMenu
from config.user_config import get_config
from src.utils.logger import get_logger

logger = get_logger("main")


class _ResultBridge(QObject):
    """백그라운드 스레드 → 메인 스레드 시그널 브릿지."""
    result_ready = pyqtSignal(object)
    free_comment_ready = pyqtSignal(object)


class VeraApp:
    """Eye of Vera 메인 애플리케이션."""

    def __init__(self):
        self._app = QApplication(sys.argv)
        self._app.setQuitOnLastWindowClosed(False)

        # 앱 아이콘 설정
        _base = getattr(sys, '_MEIPASS', os.path.abspath('.'))
        for _name in ('Eye_Of_Vera.ico', 'Eye_Of_Vera.png'):
            _icon_path = os.path.join(_base, 'assets', 'icons', _name)
            if os.path.isfile(_icon_path):
                self._app.setWindowIcon(QIcon(_icon_path))
                break

        self._config = get_config()
        self._analyzer = Analyzer()
        self._db = Database()
        self._chat = ChatWindow()
        self._chat_panel = ChatPanel(self._analyzer, self._db)
        self._report = ReportWindow(self._db)
        self._settings_panel = SettingsPanel(self._config)
        self._settings_panel.settings_saved.connect(self._on_settings_saved)
        self._log_panel = LogPanel(self._db)

        self._bridge = _ResultBridge()
        self._bridge.result_ready.connect(self._handle_result_on_main)
        self._bridge.free_comment_ready.connect(self._handle_free_comment_on_main)

        self._scheduler = Scheduler(
            analyzer=self._analyzer,
            on_result=self._on_analysis_result,
            on_free_comment=self._on_free_comment,
        )

        self._tray = TrayMenu(
            app=self._app,
            on_mission_change=self._on_mission_change,
            on_pause_resume=self._on_pause_resume,
            on_report=self._on_report,
            on_chat=self._on_chat,
            on_settings=self._on_settings,
            on_logs=self._on_logs,
            on_quit=self._on_quit,
            on_free_mode_toggle=self._on_free_mode_toggle,
        )

    def run(self):
        mission = self._ask_mission()
        if not mission:
            logger.info("작전 목표 미입력 — 종료")
            return

        self._analyzer.set_mission(mission)
        self._scheduler.start()
        logger.info("Eye of Vera 가동 완료")

        sys.exit(self._app.exec())

    def _ask_mission(self) -> str:
        text, ok = QInputDialog.getText(
            None, "Eye of Vera", "오늘의 작전 목표는 무엇입니까?"
        )
        return text.strip() if ok and text.strip() else ""

    def _on_analysis_result(self, result: AnalysisResult):
        # 백그라운드 스레드에서 호출 — DB 저장 후 시그널로 UI 전달
        self._db.insert(result, self._analyzer.mission)
        self._bridge.result_ready.emit(result)

    def _handle_result_on_main(self, result: AnalysisResult):
        self._chat.show_result(result)

    def _on_free_comment(self, result: FreeCommentResult):
        """백그라운드 스레드에서 호출 — 시그널로 메인 스레드에 전달."""
        self._bridge.free_comment_ready.emit(result)

    def _handle_free_comment_on_main(self, result: FreeCommentResult):
        """메인 스레드에서 채팅 패널에 베라의 코멘트를 표시한다."""
        self._chat_panel.receive_vera_comment(result.comment, result.screen_description)

    def _on_free_mode_toggle(self, enabled: bool):
        if enabled:
            self._scheduler.start_free_mode()
        else:
            self._scheduler.stop_free_mode()

    def _on_mission_change(self, new_mission: str):
        self._analyzer.set_mission(new_mission)

    def _on_pause_resume(self, paused: bool):
        if paused:
            self._scheduler.stop()
        else:
            self._scheduler.start()

    def _on_chat(self):
        self._chat_panel.show()
        self._chat_panel.raise_()

    def _on_report(self):
        self._report.refresh()
        self._report.show()
        self._report.raise_()

    def _on_logs(self):
        self._log_panel.show()
        self._log_panel.raise_()

    def _on_settings(self):
        self._settings_panel.show()
        self._settings_panel.raise_()

    def _on_settings_saved(self):
        """설정 저장 후 변경사항을 각 컴포넌트에 반영한다."""
        new_interval = self._config.get("monitoring", "capture_interval_minutes")
        self._scheduler.set_interval(new_interval)
        if self._scheduler.free_mode:
            free_interval = self._config.get("monitoring", "free_interaction_interval_minutes")
            self._scheduler.set_free_interval(free_interval)
        logger.info("설정 반영 완료 (캡처 주기: %d분, 모델: %s)",
                     new_interval, self._config.get("ai", "model"))

    def _on_quit(self):
        self._scheduler.shutdown()
        self._db.close()


if __name__ == "__main__":
    app = VeraApp()
    app.run()
