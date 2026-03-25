import json
from dataclasses import dataclass
from google import genai
from PIL import Image

from config.settings import GEMINI_API_KEY
from config.user_config import get_config
from src.core.prompt import build_prompt, build_chat_prompt, PROMPT_PRESETS
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AnalysisResult:
    status: str          # FOCUS | RELAX | DEVIATION
    confidence: float
    detected_activity: str
    message: str
    action_required: bool


@dataclass
class FreeCommentResult:
    comment: str
    screen_description: str


class Analyzer:
    """Gemini API를 이용하여 스크린샷을 분석한다."""

    def __init__(self):
        self._client = genai.Client(api_key=GEMINI_API_KEY)
        self._mission: str = ""

    @property
    def model(self) -> str:
        return get_config().get("ai", "model")

    @property
    def mission(self) -> str:
        return self._mission

    def set_mission(self, mission: str):
        self._mission = mission
        logger.info("작전 목표 설정: %s", mission)

    def analyze(self, image: Image.Image) -> AnalysisResult:
        if not self._mission:
            raise ValueError("작전 목표가 설정되지 않았습니다.")

        prompt = build_prompt(self._mission, custom_template=self._get_analysis_template())
        logger.info("Gemini 분석 요청 전송")

        try:
            response = self._client.models.generate_content(
                model=self.model,
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

    def free_comment(self, image: Image.Image) -> FreeCommentResult:
        """화면 스크린샷을 보고 자유롭게 코멘트한다 (자유 상호작용 모드)."""
        prompt = self._get_free_template()
        logger.info("Gemini 자유 코멘트 요청 전송")

        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=[prompt, image],
            )
            return self._parse_free_response(response.text)
        except Exception as e:
            logger.error("Gemini 자유 코멘트 API 호출 실패: %s", e)
            return FreeCommentResult(
                comment="지휘관, 통신 장애가 발생했습니다. 잠시 후 다시 시도하겠습니다.",
                screen_description="",
            )

    def chat(self, user_message: str, history: list[dict],
             context: str = "", knowledge: str = "",
             screen_context: str = "") -> str:
        """사용자 메시지에 대해 베라가 대화형으로 응답한다."""
        system_prompt = build_chat_prompt(
            self._mission or "(미설정)",
            context or "수집된 데이터 없음",
            knowledge=knowledge,
            screen_context=screen_context,
            custom_template=self._get_chat_template(),
        )

        contents = [system_prompt]
        for msg in history:
            role_prefix = "지휘관: " if msg["role"] == "user" else "베라: "
            contents.append(role_prefix + msg["text"])
        contents.append("지휘관: " + user_message)

        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=contents,
            )
            return response.text.strip()
        except Exception as e:
            logger.error("Gemini 대화 API 호출 실패: %s", e)
            return "지휘관, 통신 장애가 발생했습니다. 잠시 후 다시 시도해 주십시오."

    def _get_analysis_template(self) -> str:
        """설정에서 분석 프롬프트 템플릿을 가져온다."""
        cfg = get_config()
        custom = cfg.get("prompts", "analysis_custom")
        if custom:
            return custom
        preset_id = cfg.get("prompts", "preset")
        preset = PROMPT_PRESETS.get(preset_id, {})
        return preset.get("analysis", "")

    def _get_chat_template(self) -> str:
        """설정에서 대화 프롬프트 템플릿을 가져온다."""
        cfg = get_config()
        custom = cfg.get("prompts", "chat_custom")
        if custom:
            return custom
        preset_id = cfg.get("prompts", "preset")
        preset = PROMPT_PRESETS.get(preset_id, {})
        return preset.get("chat", "")

    def _get_free_template(self) -> str:
        """설정에서 자유 상호작용 프롬프트 템플릿을 가져온다."""
        cfg = get_config()
        preset_id = cfg.get("prompts", "preset")
        preset = PROMPT_PRESETS.get(preset_id, {})
        return preset.get("free", PROMPT_PRESETS["military"]["free"])

    def _parse_free_response(self, text: str) -> FreeCommentResult:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
            return FreeCommentResult(
                comment=data.get("comment", cleaned),
                screen_description=data.get("screen_description", ""),
            )
        except json.JSONDecodeError:
            logger.warning("자유 코멘트 JSON 파싱 실패, 원본 텍스트를 코멘트로 사용")
            return FreeCommentResult(comment=cleaned, screen_description="")

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
