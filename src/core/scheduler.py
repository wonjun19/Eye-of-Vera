from apscheduler.schedulers.background import BackgroundScheduler

from config.settings import CAPTURE_INTERVAL_MINUTES
from src.core.observer import Observer
from src.core.analyzer import Analyzer, AnalysisResult
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Scheduler:
    """Observer와 Analyzer를 주기적으로 실행하는 스케줄러."""

    def __init__(self, analyzer: Analyzer, on_result=None):
        self._observer = Observer()
        self._analyzer = analyzer
        self._on_result = on_result  # callback: (AnalysisResult) -> None
        self._scheduler = BackgroundScheduler()
        self._job = None

    def start(self):
        if not self._scheduler.running:
            self._job = self._scheduler.add_job(
                self._run_cycle,
                "interval",
                minutes=CAPTURE_INTERVAL_MINUTES,
            )
            self._scheduler.start()
            logger.info("스케줄러 가동 (간격: %d분)", CAPTURE_INTERVAL_MINUTES)
        else:
            self._scheduler.resume()
            logger.info("스케줄러 재개")
        # 시작/재개 직후 첫 분석 즉시 실행
        self._run_cycle()

    def stop(self):
        if self._scheduler.running:
            self._scheduler.pause()
            logger.info("스케줄러 일시 정지")

    def shutdown(self):
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("스케줄러 종료")

    def set_interval(self, minutes: int):
        if self._job:
            self._job.reschedule("interval", minutes=minutes)
            logger.info("캡처 간격 변경: %d분", minutes)

    def _run_cycle(self):
        logger.info("정찰 사이클 시작")
        try:
            image = self._observer.capture()
            result: AnalysisResult = self._analyzer.analyze(image)
            logger.info("분석 결과: status=%s, confidence=%.2f", result.status, result.confidence)

            if self._on_result:
                self._on_result(result)
        except Exception as e:
            logger.error("정찰 사이클 실패: %s", e)
