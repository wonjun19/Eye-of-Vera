import json
import os
from typing import Any

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(_PROJECT_ROOT, "config", "user_config.json")
KNOWLEDGE_DIR = os.path.join(_PROJECT_ROOT, "knowledge")

# ── 테마 정의 ──

THEMES = {
    "dark": {
        "name": "다크 (기본)",
        "bg": "#1a1a2e",
        "border": "#5c6bc0",
        "text": "#e0e0e0",
        "user_bubble": "#2a2a4e",
        "vera_bubble": "#1e3a2e",
        "vera_text": "#c8e6c9",
        "input_bg": "#16162a",
        "sub_border": "#3a3a5e",
        "hover": "#7986cb",
    },
    "military": {
        "name": "밀리터리 그린",
        "bg": "#1a2e1a",
        "border": "#4caf50",
        "text": "#c8e6c9",
        "user_bubble": "#2e4e2a",
        "vera_bubble": "#1e3a1e",
        "vera_text": "#a5d6a7",
        "input_bg": "#162a16",
        "sub_border": "#2e5e2e",
        "hover": "#66bb6a",
    },
    "navy": {
        "name": "네이비",
        "bg": "#0d1b2a",
        "border": "#1b9aaa",
        "text": "#d4e4f7",
        "user_bubble": "#1b2a4e",
        "vera_bubble": "#0a2e3e",
        "vera_text": "#b2ebf2",
        "input_bg": "#0a1628",
        "sub_border": "#1a3a5e",
        "hover": "#4dd0e1",
    },
}

# ── 기본 설정값 ──

DEFAULTS = {
    "monitoring": {
        "capture_interval_minutes": 5,
        "start_delay_seconds": 30,
        "free_interaction_interval_minutes": 3,
        "break_reminder": True,
        "focus_duration_minutes": 50,
        "break_duration_minutes": 10,
        "keep_screenshots": False,
        "screenshot_retention_hours": 24,
    },
    "ai": {
        "model": "gemini-3.1-flash-lite-preview",
    },
    "prompts": {
        "preset": "military",
        "analysis_custom": "",
        "chat_custom": "",
    },
    "knowledge": {
        "enabled_files": [],
    },
    "appearance": {
        "theme": "dark",
        "default_opacity": 95,
        "base_font_size": 10,
    },
}


class UserConfig:
    """JSON 기반 사용자 설정 관리."""

    def __init__(self):
        self._data: dict = {}
        self._load()

    def _load(self):
        if os.path.isfile(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._data = {}

        # 누락된 키는 기본값으로 채움
        for section, defaults in DEFAULTS.items():
            if section not in self._data:
                self._data[section] = {}
            for key, value in defaults.items():
                if key not in self._data[section]:
                    self._data[section][key] = value

    def save(self):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def get(self, section: str, key: str) -> Any:
        return self._data.get(section, {}).get(
            key, DEFAULTS.get(section, {}).get(key)
        )

    def set(self, section: str, key: str, value: Any):
        if section not in self._data:
            self._data[section] = {}
        self._data[section][key] = value

    def get_theme(self) -> dict:
        theme_id = self.get("appearance", "theme")
        return THEMES.get(theme_id, THEMES["dark"])


# ── 싱글턴 접근자 ──

_instance: UserConfig | None = None


def get_config() -> UserConfig:
    global _instance
    if _instance is None:
        _instance = UserConfig()
    return _instance
