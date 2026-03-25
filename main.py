import sys
from PyQt6.QtWidgets import QApplication, QInputDialog
from PyQt6.QtCore import QObject, pyqtSignal

from src.core.analyzer import Analyzer, AnalysisResult
from src.core.database import Database
from src.core.scheduler import Scheduler
from src.ui.chat_window import ChatWindow
from src.ui.report_window import ReportWindow
from src.ui.tray_menu import TrayMenu
from src.utils.logger import get_logger

logger = get_logger("main")


class _ResultBridge(QObject):
    """백그라운드 스레드 → 메인 스레드 시그널 브릿지."""
    result_ready = pyqtSignal(object)


class VeraApp:
    """Eye of Vera 메인 애플리케이션."""

    def __init__(self):
        self._app = QApplication(sys.argv)
        self._app.setQuitOnLastWindowClosed(False)

        self._analyzer = Analyzer()
        self._db = Database()
        self._chat = ChatWindow()
        self._report = ReportWindow(self._db)

        self._bridge = _ResultBridge()
        self._bridge.result_ready.connect(self._handle_result_on_main)

        self._scheduler = Scheduler(
            analyzer=self._analyzer,
            on_result=self._on_analysis_result,
        )

        self._tray = TrayMenu(
            app=self._app,
            on_mission_change=self._on_mission_change,
            on_pause_resume=self._on_pause_resume,
            on_report=self._on_report,
            on_quit=self._on_quit,
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

    def _on_mission_change(self, new_mission: str):
        self._analyzer.set_mission(new_mission)

    def _on_pause_resume(self, paused: bool):
        if paused:
            self._scheduler.stop()
        else:
            self._scheduler.start()

    def _on_report(self):
        self._report.refresh()
        self._report.show()
        self._report.raise_()

    def _on_quit(self):
        self._scheduler.shutdown()
        self._db.close()


if __name__ == "__main__":
    app = VeraApp()
    app.run()
