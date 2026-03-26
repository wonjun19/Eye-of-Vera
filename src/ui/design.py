"""VERA-OS 디자인 토큰 — 공유 스타일 상수 (PyQt6 구현체).

모든 UI 컴포넌트는 이 모듈의 토큰을 참조합니다.
색상 변경은 이 파일 한 곳에서만 수행하십시오.
"""

# ── 폰트 ──
FONT_MONO = "Consolas"
FONT_UI   = "맑은 고딕"

# ── 상태별 디자인 토큰 ──
STATUS: dict[str, dict[str, str]] = {
    "FOCUS": {
        "bg":     "#0c1e10",
        "bg2":    "#172c1c",
        "border": "#43a047",
        "accent": "#66bb6a",
        "text":   "#c8e6c9",
        "badge_bg": "#1b5e20",
        "icon":   "◉",
        "label":  "집중",
    },
    "RELAX": {
        "bg":     "#0c1224",
        "bg2":    "#16203c",
        "border": "#5c6bc0",
        "accent": "#7986cb",
        "text":   "#c5cae9",
        "badge_bg": "#1a237e",
        "icon":   "◐",
        "label":  "휴식",
    },
    "DEVIATION": {
        "bg":     "#200c0c",
        "bg2":    "#301414",
        "border": "#e53935",
        "accent": "#ef5350",
        "text":   "#ffcdd2",
        "badge_bg": "#b71c1c",
        "icon":   "⚠",
        "label":  "이탈",
    },
    "UNKNOWN": {
        "bg":     "#12121e",
        "bg2":    "#1a1a2e",
        "border": "#616161",
        "accent": "#757575",
        "text":   "#bdbdbd",
        "badge_bg": "#37474f",
        "icon":   "○",
        "label":  "–",
    },
}

STATUS_COLORS = {k: v["border"] for k, v in STATUS.items()}
STATUS_LABELS = {k: v["label"]  for k, v in STATUS.items()}
STATUS_ICONS  = {k: v["icon"]   for k, v in STATUS.items()}

# ── 폰트 사이즈 ──
TEXT_XS   = 8
TEXT_SM   = 9
TEXT_BASE = 10
TEXT_MD   = 11
TEXT_LG   = 12
TEXT_XL   = 14

# ── 스페이싱 & 셰이프 ──
RADIUS_SM = 6
RADIUS_MD = 10
RADIUS_LG = 14

GAP_XS = 4
GAP_SM = 8
GAP_MD = 12
GAP_LG = 16
GAP_XL = 24

# ── 애니메이션 ──
DURATION_FAST   = 200
DURATION_NORMAL = 400
DURATION_SLOW   = 800
PULSE_INTERVAL  = 30

# ── 공통 스크롤바 스타일 (테마 bg/border 주입용) ──
def scrollbar_style(bg: str, handle: str) -> str:
    return (
        f"QScrollBar:vertical {{ background: {bg}; width: 6px; border: none; }}"
        f"QScrollBar::handle:vertical {{ background: {handle}; border-radius: 3px; min-height: 20px; }}"
        "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
    )
