"""음성 대사 재생 모듈.

분석 결과 상태(FOCUS / DEVIATION)에 맞는 대사를 랜덤으로 골라 재생한다.
RELAX 상태에서는 재생하지 않는다.
"""

import os
import random

from PyQt6.QtCore import QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

from config.user_config import get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)

_BASE = os.path.join(
    getattr(__import__("sys"), "_MEIPASS", os.path.abspath(".")),
    "assets",
    "Dialogue preset",
)

# 상태별 대사 파일 매핑
DIALOGUE_MAP: dict[str, list[str]] = {
    "FOCUS": [
        "훌륭합니다, 계속 진행하세요.mp3",
        "현재 페이스를 유지하세요.mp3",
    ],
    "DEVIATION": [
        "이탈이 감지되었습니다.mp3",
        "집중하세요.mp3",
    ],
}


class DialoguePlayer:
    """상태 기반 음성 대사 플레이어."""

    def __init__(self):
        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)
        self._apply_volume()

    def _apply_volume(self):
        """설정에서 볼륨을 읽어 적용한다."""
        cfg = get_config()
        volume = cfg.get("audio", "volume") / 100.0
        enabled = cfg.get("audio", "enabled")
        self._audio_output.setVolume(volume if enabled else 0.0)

    def play_for_status(self, status: str):
        """분석 상태에 따라 대사를 재생한다. RELAX/UNKNOWN은 무시."""
        cfg = get_config()
        if not cfg.get("audio", "enabled"):
            return

        files = DIALOGUE_MAP.get(status)
        if not files:
            return

        chosen = random.choice(files)
        path = os.path.join(_BASE, chosen)

        if not os.path.isfile(path):
            logger.warning("대사 파일 없음: %s", path)
            return

        self._apply_volume()
        self._player.setSource(QUrl.fromLocalFile(path))
        self._player.play()
        logger.info("대사 재생: [%s] %s", status, chosen)

    def play_test(self):
        """설정 패널에서 볼륨 테스트용으로 FOCUS 대사 하나를 재생한다."""
        files = DIALOGUE_MAP["FOCUS"]
        chosen = random.choice(files)
        path = os.path.join(_BASE, chosen)

        if not os.path.isfile(path):
            logger.warning("테스트 대사 파일 없음: %s", path)
            return

        self._apply_volume()
        self._player.setSource(QUrl.fromLocalFile(path))
        self._player.play()
        logger.info("테스트 대사 재생: %s", chosen)
