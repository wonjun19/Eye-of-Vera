import json
from dataclasses import dataclass
from google import genai
from PIL import Image

from config.settings import GEMINI_API_KEY, GEMINI_MODEL
from src.core.prompt import build_prompt
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AnalysisResult:
    status: str          # FOCUS | RELAX | DEVIATION
    confidence: float
    detected_activity: str
    message: str
    action_required: bool


class Analyzer:
    """Gemini API를 이용하여 스크린샷을 분석한다."""

    def __init__(self):
        self._client = genai.Client(api_key=GEMINI_API_KEY)
        self._model = GEMINI_MODEL
        self._mission: str = ""

    @property
    def mission(self) -> str:
        return self._mission

    def set_mission(self, mission: str):
        self._mission = mission
        logger.info("작전 목표 설정: %s", mission)

    def analyze(self, image: Image.Image) -> AnalysisResult:
        if not self._mission:
            raise ValueError("작전 목표가 설정되지 않았습니다.")

        prompt = build_prompt(self._mission)
        logger.info("Gemini 분석 요청 전송")

        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=[prompt, image],
            )
            return self._parse_response(response.text)
        except Exception as e:
            logger.error("Gemini API 호출 실패: %s", e)
            return AnalysisResult(
                status="UNKNOWN",
                confidence=0.0,
                detected_activity="분석 실패",
                message="지휘관, 통신 장애가 발생했습니다. 다음 정찰 시 재시도하겠습니다.",
                action_required=False,
            )

    def _parse_response(self, text: str) -> AnalysisResult:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("JSON 파싱 실패, 원본: %s", text[:200])
            return AnalysisResult(
                status="UNKNOWN",
                confidence=0.0,
                detected_activity="응답 파싱 실패",
                message="지휘관, 분석 데이터 해석에 실패했습니다. 다음 정찰 시 재시도하겠습니다.",
                action_required=False,
            )

        return AnalysisResult(
            status=data.get("status", "UNKNOWN"),
            confidence=float(data.get("confidence", 0.0)),
            detected_activity=data.get("detected_activity", ""),
            message=data.get("message", ""),
            action_required=bool(data.get("action_required", False)),
        )
