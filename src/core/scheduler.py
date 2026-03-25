from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from config.settings import CAPTURE_INTERVAL_MINUTES
from config.user_config import get_config
from src.core.observer import Observer
from src.core.analyzer import Analyzer, AnalysisResult, FreeCommentResult
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Scheduler:
    """Observer와 Analyzer를 주기적으로 실행하는 스케줄러."""

    def __init__(self, analyzer: Analyzer, on_result=None, on_free_comment=None):
        self._observer = Observer()
        self._analyzer = analyzer
        self._on_result = on_result  # callback: (AnalysisResult) -> None
        self._on_free_comment = on_free_comment  # callback: (str) -> None
        self._scheduler = BackgroundScheduler()
        self._job = None
        self._free_job = None
        self._free_mode = False

    # ── 정찰 모드 ──

    def start(self):
        if not self._scheduler.running:
            delay = get_config().get("monitoring", "start_delay_seconds")
            first_run = datetime.now() + timedelta(seconds=delay)
            self._job = self._scheduler.add_job(
                self._run_cycle,
                "interval",
                minutes=CAPTURE_INTERVAL_MINUTES,
                next_run_time=first_run,
            )
            self._scheduler.start()
            logger.info("스케줄러 가동 (첫 캡처: %d초 후, 간격: %d분)", delay, CAPTURE_INTERVAL_MINUTES)
        else:
            self._scheduler.resume()
            logger.info("스케줄러 재개")

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

    # ── 자유 상호작용 모드 ──

    @property
    def free_mode(self) -> bool:
        return self._free_mode

    def start_free_mode(self):
        """자유 상호작용 모드를 시작한다. 정찰 모드는 자동 정지."""
        self._free_mode = True

        # 정찰 job 일시 정지
        if self._job:
            self._job.pause()
            logger.info("정찰 모드 일시 정지 (자유 상호작용 모드 전환)")

        # 스케줄러가 아직 시작되지 않았으면 시작
        if not self._scheduler.running:
            self._scheduler.start()

        cfg = get_config()
        interval = cfg.get("monitoring", "free_interaction_interval_minutes")
        delay = cfg.get("monitoring", "start_delay_seconds")
        first_run = datetime.now() + timedelta(seconds=delay)

        self._free_job = self._scheduler.add_job(
            self._run_free_cycle,
            "interval",
            minutes=interval,
            next_run_time=first_run,
        )
        logger.info("자유 상호작용 모드 가동 (첫 코멘트: %d초 후, 간격: %d분)", delay, interval)

    def stop_free_mode(self):
        """자유 상호작용 모드를 종료하고 정찰 모드로 복귀한다."""
        self._free_mode = False

        if self._free_job:
            self._free_job.remove()
            self._free_job = None
            logger.info("자유 상호작용 모드 종료")

        # 정찰 job 재개
        if self._job:
            self._job.resume()
            logger.info("정찰 모드 재개")

    def set_free_interval(self, minutes: int):
        if self._free_job:
            self._free_job.reschedule("interval", minutes=minutes)
            logger.info("자유 상호작용 간격 변경: %d분", minutes)

    # ── 사이클 ──

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

    def _run_free_cycle(self):
        logger.info("자유 상호작용 사이클 시작")
        try:
            image = self._observer.capture()
            result: FreeCommentResult = self._analyzer.free_comment(image)
            logger.info("자유 코멘트: %s", result.comment[:80])

            if self._on_free_comment:
                self._on_free_comment(result)
        except Exception as e:
            logger.error("자유 상호작용 사이클 실패: %s", e)
