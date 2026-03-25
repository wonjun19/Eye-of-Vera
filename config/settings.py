import os
from dotenv import load_dotenv

load_dotenv()

# Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite-preview")

# 캡처 주기 (분)
CAPTURE_INTERVAL_MINUTES = int(os.getenv("CAPTURE_INTERVAL_MINUTES", "5"))

# 오버레이 UI
OVERLAY_OPACITY = float(os.getenv("OVERLAY_OPACITY", "0.9"))
OVERLAY_FADE_SECONDS = 5
OVERLAY_POSITION = "bottom_right"

# 보안: 캡처 이미지 보관 여부 (False = 분석 후 즉시 삭제)
KEEP_SCREENSHOTS = os.getenv("KEEP_SCREENSHOTS", "false").lower() == "true"
SCREENSHOT_RETENTION_HOURS = 24

# 휴식 알림: 50분 집중 후 10분 휴식 권고
BREAK_TIME_REMINDER = os.getenv("BREAK_TIME_REMINDER", "true").lower() == "true"
FOCUS_DURATION_MINUTES = 50
BREAK_DURATION_MINUTES = 10

# 로그
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "vera.db")
