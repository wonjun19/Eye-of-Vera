from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel,
    QSpinBox, QCheckBox, QComboBox, QTextEdit, QLineEdit,
    QPushButton, QSlider, QListWidget, QListWidgetItem,
    QFileDialog, QMessageBox, QGroupBox, QFormLayout, QScrollArea,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from config.user_config import UserConfig, THEMES, get_config
from src.core.prompt import PROMPT_PRESETS, get_preset_names
from src.core.knowledge import (
    load_knowledge_files, add_knowledge_file,
    delete_knowledge_file, update_tags,
)
from src.ui.design import FONT_MONO, FONT_UI
from src.core.audio import DialoguePlayer
from src.utils.logger import get_logger

logger = get_logger(__name__)

GEMINI_MODELS = [
    ("gemini-3.1-flash-lite-preview", "Gemini 3.1 Flash Lite (기본)"),
    ("gemini-3-flash-preview",        "Gemini 3 Flash"),
    ("gemini-2.5-flash",              "Gemini 2.5 Flash"),
    ("gemini-3.1-pro-preview",        "Gemini 3.1 Pro"),
]

PANEL_STYLE = """
QWidget {{ background: {bg}; color: {text}; font-family: "맑은 고딕", sans-serif; }}
QTabWidget::pane {{
    border: 1px solid {sub_border}; border-radius: 0 6px 6px 6px; background: {bg};
    border-top: 2px solid {border};
}}
QTabBar::tab {{
    background: {input_bg}; color: {text};
    padding: 9px 18px; margin-right: 2px;
    border: 1px solid {sub_border};
    border-bottom: none;
    border-top-left-radius: 6px; border-top-right-radius: 6px;
    font-family: Consolas; font-size: 9pt;
}}
QTabBar::tab:selected {{
    background: {bg}; color: {border};
    border-color: {border}; border-bottom: 2px solid {bg};
    border-top: 2px solid {border};
    font-weight: bold;
}}
QTabBar::tab:hover:!selected {{ background: {bg}; }}
QGroupBox {{
    color: {border}; border: 1px solid {sub_border};
    border-radius: 8px; margin-top: 14px; padding-top: 18px;
    font-family: Consolas; font-weight: bold; font-size: 9pt;
    border-left: 2px solid {border};
}}
QGroupBox::title {{
    subcontrol-origin: margin; left: 14px; padding: 0 6px;
    background: {bg};
}}
QSpinBox, QComboBox, QLineEdit {{
    background: {input_bg}; color: {text};
    border: 1px solid {sub_border}; border-radius: 5px;
    padding: 5px 9px; min-height: 26px;
}}
QSpinBox:focus, QComboBox:focus, QLineEdit:focus {{
    border-color: {border};
}}
QTextEdit {{
    background: {input_bg}; color: {text};
    border: 1px solid {sub_border}; border-radius: 5px; padding: 6px;
}}
QTextEdit:focus {{ border-color: {border}; }}
QCheckBox {{ color: {text}; spacing: 8px; }}
QCheckBox::indicator {{
    width: 16px; height: 16px;
    border: 1.5px solid {sub_border}; border-radius: 4px;
    background: {input_bg};
}}
QCheckBox::indicator:hover {{ border-color: {border}; }}
QCheckBox::indicator:checked {{
    background: {border}; border-color: {border};
}}
QPushButton {{
    background: {border}; color: white; border: none;
    border-radius: 6px; padding: 8px 18px; font-weight: bold;
    font-family: Consolas;
}}
QPushButton:hover {{ background: {hover}; }}
QPushButton:pressed {{ background: {sub_border}; }}
QPushButton#danger {{ background: #b71c1c; border: 1px solid #e53935; }}
QPushButton#danger:hover {{ background: #c62828; }}
QPushButton#secondary {{
    background: transparent; color: {text};
    border: 1px solid {sub_border};
}}
QPushButton#secondary:hover {{ background: {input_bg}; border-color: {border}; }}
QSlider::groove:horizontal {{
    background: {sub_border}; height: 4px; border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {border}; width: 14px; height: 14px;
    margin: -5px 0; border-radius: 7px;
}}
QSlider::handle:horizontal:hover {{ background: {hover}; }}
QListWidget {{
    background: {input_bg}; color: {text};
    border: 1px solid {sub_border}; border-radius: 5px;
    outline: 0;
}}
QListWidget::item {{ padding: 6px 8px; border-radius: 3px; }}
QListWidget::item:selected {{ background: {sub_border}; color: {text}; }}
QListWidget::item:hover:!selected {{ background: {bg}; }}
QScrollBar:vertical {{
    background: {input_bg}; width: 7px; border: none;
}}
QScrollBar::handle:vertical {{
    background: {sub_border}; border-radius: 4px; min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""


class SettingsPanel(QWidget):
    """설정 패널 (정찰 설정 · 프롬프트 편집 · 지식 관리 · 외형)."""

    settings_saved = pyqtSignal()

    def __init__(self, config: UserConfig | None = None, dialogue_player: DialoguePlayer | None = None):
        super().__init__()
        self._config = config or get_config()
        self._dialogue_player = dialogue_player
        self._init_ui()
        self._load_to_ui()

    # ── UI 구성 ──

    def _init_ui(self):
        self.setWindowTitle("VERA — 설정")
        self.setMinimumSize(540, 520)
        self.resize(580, 640)
        self.setWindowFlags(
            Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self._apply_style()

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(12)

        # 헤더 라벨
        header = QLabel("VERA — 설정")
        header.setFont(QFont(FONT_MONO, 11, QFont.Weight.Bold))
        root.addWidget(header)

        # 탭
        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_monitoring_tab(), "정찰 설정")
        self._tabs.addTab(self._build_prompt_tab(),     "프롬프트 편집")
        self._tabs.addTab(self._build_knowledge_tab(),  "지식 관리")
        self._tabs.addTab(self._build_audio_tab(),      "음성")
        self._tabs.addTab(self._build_appearance_tab(), "외형")
        root.addWidget(self._tabs, stretch=1)

        # 하단 버튼
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self._save_btn = QPushButton("저장  ✓")
        self._save_btn.setFixedWidth(110)
        self._save_btn.clicked.connect(self._save_from_ui)
        btn_row.addWidget(self._save_btn)

        root.addLayout(btn_row)

    def _apply_style(self):
        theme = self._config.get_theme()
        self.setStyleSheet(PANEL_STYLE.format(**theme))

    # ────────────────────────────────────
    # 탭 1: 정찰 설정
    # ────────────────────────────────────

    def _build_monitoring_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)

        # AI 모델
        grp_model = QGroupBox("AI 모델")
        form_model = QFormLayout(grp_model)
        self._model_combo = QComboBox()
        for model_id, display in GEMINI_MODELS:
            self._model_combo.addItem(display, model_id)
        form_model.addRow("Gemini 모델:", self._model_combo)
        layout.addWidget(grp_model)

        # 캡처 주기
        grp1 = QGroupBox("캡처 주기")
        form1 = QFormLayout(grp1)
        self._capture_interval = QSpinBox()
        self._capture_interval.setRange(1, 30)
        self._capture_interval.setSuffix(" 분")
        form1.addRow("정찰 간격:", self._capture_interval)
        self._start_delay = QSpinBox()
        self._start_delay.setRange(0, 600)
        self._start_delay.setSuffix(" 초")
        self._start_delay.setToolTip("프로그램 시작 후 첫 캡처까지 대기 시간 (0 = 즉시)")
        form1.addRow("시작 지연:", self._start_delay)
        self._free_interval = QSpinBox()
        self._free_interval.setRange(1, 30)
        self._free_interval.setSuffix(" 분")
        self._free_interval.setToolTip("자유 상호작용 모드에서 화면 캡처 간격")
        form1.addRow("자유 상호작용 간격:", self._free_interval)
        layout.addWidget(grp1)

        # 휴식 알림
        grp2 = QGroupBox("휴식 알림")
        vbox2 = QVBoxLayout(grp2)
        self._break_reminder = QCheckBox("휴식 알림 활성화")
        vbox2.addWidget(self._break_reminder)
        form2 = QFormLayout()
        self._focus_duration = QSpinBox()
        self._focus_duration.setRange(10, 120)
        self._focus_duration.setSuffix(" 분")
        form2.addRow("집중 시간:", self._focus_duration)
        self._break_duration = QSpinBox()
        self._break_duration.setRange(1, 30)
        self._break_duration.setSuffix(" 분")
        form2.addRow("휴식 시간:", self._break_duration)
        vbox2.addLayout(form2)
        self._break_reminder.toggled.connect(self._focus_duration.setEnabled)
        self._break_reminder.toggled.connect(self._break_duration.setEnabled)
        layout.addWidget(grp2)

        # 스크린샷 보관
        grp3 = QGroupBox("스크린샷 보관")
        vbox3 = QVBoxLayout(grp3)
        self._keep_screenshots = QCheckBox("분석 후 스크린샷 보관")
        vbox3.addWidget(self._keep_screenshots)
        form3 = QFormLayout()
        self._retention_hours = QSpinBox()
        self._retention_hours.setRange(1, 168)
        self._retention_hours.setSuffix(" 시간")
        form3.addRow("보관 기간:", self._retention_hours)
        vbox3.addLayout(form3)
        self._keep_screenshots.toggled.connect(self._retention_hours.setEnabled)
        layout.addWidget(grp3)

        layout.addStretch()
        return tab

    # ────────────────────────────────────
    # 탭 2: 프롬프트 편집
    # ────────────────────────────────────

    def _build_prompt_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        # 프리셋 선택
        preset_row = QHBoxLayout()
        preset_row.addWidget(QLabel("프리셋:"))
        self._preset_combo = QComboBox()
        for pid, name in get_preset_names().items():
            self._preset_combo.addItem(name, pid)
        self._preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        preset_row.addWidget(self._preset_combo, stretch=1)

        self._preset_reset_btn = QPushButton("초기화")
        self._preset_reset_btn.setObjectName("secondary")
        self._preset_reset_btn.setFixedWidth(72)
        self._preset_reset_btn.clicked.connect(self._reset_prompts)
        preset_row.addWidget(self._preset_reset_btn)
        layout.addLayout(preset_row)

        # 분석 프롬프트
        layout.addWidget(QLabel("분석 프롬프트 (스크린샷 판별):"))
        self._analysis_prompt = QTextEdit()
        self._analysis_prompt.setFont(QFont(FONT_MONO, 9))
        self._analysis_prompt.setMinimumHeight(140)
        layout.addWidget(self._analysis_prompt, stretch=1)

        # 대화 프롬프트
        layout.addWidget(QLabel("대화 프롬프트 (채팅):"))
        self._chat_prompt = QTextEdit()
        self._chat_prompt.setFont(QFont(FONT_MONO, 9))
        self._chat_prompt.setMinimumHeight(140)
        layout.addWidget(self._chat_prompt, stretch=1)

        hint = QLabel("※ {mission}, {context}, {knowledge}는 자동 치환됩니다.")
        hint.setStyleSheet(f"color: #666; font-size: 9px; font-family: {FONT_MONO};")
        layout.addWidget(hint)

        return tab

    def _on_preset_changed(self, index: int):
        pid = self._preset_combo.itemData(index)
        if pid and pid in PROMPT_PRESETS:
            preset = PROMPT_PRESETS[pid]
            self._analysis_prompt.setPlainText(preset["analysis"])
            self._chat_prompt.setPlainText(preset["chat"])

    def _reset_prompts(self):
        self._on_preset_changed(self._preset_combo.currentIndex())

    # ────────────────────────────────────
    # 탭 3: 지식 관리
    # ────────────────────────────────────

    def _build_knowledge_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        layout.addWidget(QLabel("knowledge/ 폴더의 지식 파일 (체크 = 활성화):"))

        # 파일 목록
        self._knowledge_list = QListWidget()
        self._knowledge_list.currentRowChanged.connect(self._on_knowledge_selected)
        layout.addWidget(self._knowledge_list, stretch=1)

        # 버튼 행
        btn_row = QHBoxLayout()
        add_btn = QPushButton("파일 추가")
        add_btn.setObjectName("secondary")
        add_btn.clicked.connect(self._add_knowledge)
        btn_row.addWidget(add_btn)

        del_btn = QPushButton("삭제")
        del_btn.setObjectName("danger")
        del_btn.clicked.connect(self._delete_knowledge)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # 태그 편집
        tag_row = QHBoxLayout()
        tag_row.addWidget(QLabel("태그:"))
        self._tag_edit = QLineEdit()
        self._tag_edit.setPlaceholderText("쉼표로 구분 (예: 집중, 생산성, 뽀모도로)")
        tag_row.addWidget(self._tag_edit, stretch=1)
        tag_apply_btn = QPushButton("태그 저장")
        tag_apply_btn.setObjectName("secondary")
        tag_apply_btn.setFixedWidth(80)
        tag_apply_btn.clicked.connect(self._save_tags)
        tag_row.addWidget(tag_apply_btn)
        layout.addLayout(tag_row)

        # 미리보기
        layout.addWidget(QLabel("미리보기:"))
        self._knowledge_preview = QTextEdit()
        self._knowledge_preview.setReadOnly(True)
        self._knowledge_preview.setFont(QFont(FONT_MONO, 9))
        self._knowledge_preview.setMaximumHeight(140)
        layout.addWidget(self._knowledge_preview)

        return tab

    def _refresh_knowledge_list(self):
        self._knowledge_list.clear()
        enabled = self._config.get("knowledge", "enabled_files") or []
        self._knowledge_files = load_knowledge_files()
        for f in self._knowledge_files:
            item = QListWidgetItem(f["name"])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked if f["name"] in enabled
                else Qt.CheckState.Unchecked
            )
            self._knowledge_list.addItem(item)

    def _on_knowledge_selected(self, row: int):
        if row < 0 or row >= len(self._knowledge_files):
            self._tag_edit.clear()
            self._knowledge_preview.clear()
            return
        f = self._knowledge_files[row]
        self._tag_edit.setText(", ".join(f["tags"]))
        self._knowledge_preview.setPlainText(f["body"][:2000])

    def _add_knowledge(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "지식 파일 추가", "",
            "Text files (*.md *.txt);;All files (*)",
        )
        for path in paths:
            add_knowledge_file(path)
        self._refresh_knowledge_list()

    def _delete_knowledge(self):
        item = self._knowledge_list.currentItem()
        if not item:
            return
        name = item.text()
        reply = QMessageBox.question(
            self, "삭제 확인",
            f"'{name}' 파일을 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            delete_knowledge_file(name)
            self._refresh_knowledge_list()

    def _save_tags(self):
        item = self._knowledge_list.currentItem()
        if not item:
            return
        row = self._knowledge_list.currentRow()
        name = item.text()
        tags = [t.strip() for t in self._tag_edit.text().split(",") if t.strip()]
        update_tags(name, tags)
        # 로컬 캐시 갱신
        self._knowledge_files[row]["tags"] = tags

    # ────────────────────────────────────
    # 탭 4: 음성
    # ────────────────────────────────────

    def _build_audio_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)

        # 음성 활성화
        grp1 = QGroupBox("음성 대사")
        vbox1 = QVBoxLayout(grp1)
        self._audio_enabled = QCheckBox("음성 대사 활성화")
        vbox1.addWidget(self._audio_enabled)

        hint = QLabel("분석 결과에 따라 베라의 음성 대사가 재생됩니다.\n"
                       "FOCUS(집중) · DEVIATION(이탈) 상태에서만 재생되며,\n"
                       "RELAX(휴식) 상태에서는 재생되지 않습니다.")
        hint.setStyleSheet(f"color: #888; font-size: 9px; font-family: {FONT_MONO};")
        vbox1.addWidget(hint)
        layout.addWidget(grp1)

        # 볼륨
        grp2 = QGroupBox("음성 크기")
        vbox2 = QVBoxLayout(grp2)
        vol_row = QHBoxLayout()
        self._volume_slider = QSlider(Qt.Orientation.Horizontal)
        self._volume_slider.setRange(0, 100)
        self._volume_label = QLabel("70%")
        self._volume_slider.valueChanged.connect(
            lambda v: self._volume_label.setText(f"{v}%")
        )
        vol_row.addWidget(self._volume_slider, stretch=1)
        vol_row.addWidget(self._volume_label)
        vbox2.addLayout(vol_row)

        # 테스트 버튼
        self._audio_test_btn = QPushButton("음성 크기 테스트  ▶")
        self._audio_test_btn.setObjectName("secondary")
        self._audio_test_btn.setFixedWidth(160)
        self._audio_test_btn.clicked.connect(self._test_audio)
        vbox2.addWidget(self._audio_test_btn)
        layout.addWidget(grp2)

        # 연결: 활성화 체크박스로 볼륨 슬라이더/테스트 버튼 활성화 제어
        self._audio_enabled.toggled.connect(self._volume_slider.setEnabled)
        self._audio_enabled.toggled.connect(self._audio_test_btn.setEnabled)

        layout.addStretch()
        return tab

    def _test_audio(self):
        """현재 슬라이더 볼륨으로 테스트 대사를 재생한다."""
        # 슬라이더 값을 임시로 설정에 반영
        cfg = self._config
        cfg.set("audio", "volume", self._volume_slider.value())
        cfg.set("audio", "enabled", True)

        if self._dialogue_player:
            self._dialogue_player.play_test()

    # ────────────────────────────────────
    # 탭 5: 외형
    # ────────────────────────────────────

    def _build_appearance_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)

        # 테마 선택
        grp1 = QGroupBox("테마")
        form1 = QFormLayout(grp1)
        self._theme_combo = QComboBox()
        for tid, tdata in THEMES.items():
            self._theme_combo.addItem(tdata["name"], tid)
        form1.addRow("컬러 테마:", self._theme_combo)
        layout.addWidget(grp1)

        # 투명도
        grp2 = QGroupBox("채팅창 기본 투명도")
        vbox2 = QVBoxLayout(grp2)
        opacity_row = QHBoxLayout()
        self._opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._opacity_slider.setRange(30, 100)
        self._opacity_label = QLabel("95%")
        self._opacity_slider.valueChanged.connect(
            lambda v: self._opacity_label.setText(f"{v}%")
        )
        opacity_row.addWidget(self._opacity_slider, stretch=1)
        opacity_row.addWidget(self._opacity_label)
        vbox2.addLayout(opacity_row)
        layout.addWidget(grp2)

        # 폰트 크기
        grp3 = QGroupBox("기본 폰트 크기")
        form3 = QFormLayout(grp3)
        self._font_size = QSpinBox()
        self._font_size.setRange(8, 16)
        self._font_size.setSuffix(" pt")
        form3.addRow("채팅 텍스트:", self._font_size)
        layout.addWidget(grp3)

        layout.addStretch()

        hint = QLabel("※ 테마 변경은 채팅창을 다시 열면 적용됩니다.")
        hint.setStyleSheet(f"color: #666; font-size: 9px; font-family: {FONT_MONO};")
        layout.addWidget(hint)

        return tab

    # ── 설정 로드 / 저장 ──

    def _load_to_ui(self):
        cfg = self._config

        # AI 모델
        current_model = cfg.get("ai", "model")
        idx = self._model_combo.findData(current_model)
        if idx >= 0:
            self._model_combo.setCurrentIndex(idx)

        # 정찰 설정
        self._capture_interval.setValue(cfg.get("monitoring", "capture_interval_minutes"))
        self._start_delay.setValue(cfg.get("monitoring", "start_delay_seconds"))
        self._free_interval.setValue(cfg.get("monitoring", "free_interaction_interval_minutes"))
        self._break_reminder.setChecked(cfg.get("monitoring", "break_reminder"))
        self._focus_duration.setValue(cfg.get("monitoring", "focus_duration_minutes"))
        self._break_duration.setValue(cfg.get("monitoring", "break_duration_minutes"))
        self._focus_duration.setEnabled(cfg.get("monitoring", "break_reminder"))
        self._break_duration.setEnabled(cfg.get("monitoring", "break_reminder"))
        self._keep_screenshots.setChecked(cfg.get("monitoring", "keep_screenshots"))
        self._retention_hours.setValue(cfg.get("monitoring", "screenshot_retention_hours"))
        self._retention_hours.setEnabled(cfg.get("monitoring", "keep_screenshots"))

        # 프롬프트
        preset_id = cfg.get("prompts", "preset")
        idx = self._preset_combo.findData(preset_id)
        if idx >= 0:
            self._preset_combo.setCurrentIndex(idx)

        # 커스텀 프롬프트가 있으면 그걸 표시, 없으면 프리셋
        analysis_custom = cfg.get("prompts", "analysis_custom")
        chat_custom = cfg.get("prompts", "chat_custom")
        if analysis_custom:
            self._analysis_prompt.setPlainText(analysis_custom)
        else:
            self._on_preset_changed(idx if idx >= 0 else 0)

        if chat_custom:
            self._chat_prompt.setPlainText(chat_custom)

        # 지식 관리
        self._knowledge_files = []
        self._refresh_knowledge_list()

        # 음성
        self._audio_enabled.setChecked(cfg.get("audio", "enabled"))
        self._volume_slider.setValue(cfg.get("audio", "volume"))
        self._volume_slider.setEnabled(cfg.get("audio", "enabled"))
        self._audio_test_btn.setEnabled(cfg.get("audio", "enabled"))

        # 외형
        theme_id = cfg.get("appearance", "theme")
        tidx = self._theme_combo.findData(theme_id)
        if tidx >= 0:
            self._theme_combo.setCurrentIndex(tidx)
        self._opacity_slider.setValue(cfg.get("appearance", "default_opacity"))
        self._font_size.setValue(cfg.get("appearance", "base_font_size"))

    def _save_from_ui(self):
        cfg = self._config

        # AI 모델
        cfg.set("ai", "model", self._model_combo.currentData())

        # 정찰 설정
        cfg.set("monitoring", "capture_interval_minutes", self._capture_interval.value())
        cfg.set("monitoring", "start_delay_seconds", self._start_delay.value())
        cfg.set("monitoring", "free_interaction_interval_minutes", self._free_interval.value())
        cfg.set("monitoring", "break_reminder", self._break_reminder.isChecked())
        cfg.set("monitoring", "focus_duration_minutes", self._focus_duration.value())
        cfg.set("monitoring", "break_duration_minutes", self._break_duration.value())
        cfg.set("monitoring", "keep_screenshots", self._keep_screenshots.isChecked())
        cfg.set("monitoring", "screenshot_retention_hours", self._retention_hours.value())

        # 프롬프트
        preset_id = self._preset_combo.currentData()
        cfg.set("prompts", "preset", preset_id)

        # 프리셋과 다르면 커스텀으로 저장
        preset = PROMPT_PRESETS.get(preset_id, {})
        analysis_text = self._analysis_prompt.toPlainText()
        chat_text = self._chat_prompt.toPlainText()

        if analysis_text != preset.get("analysis", ""):
            cfg.set("prompts", "analysis_custom", analysis_text)
        else:
            cfg.set("prompts", "analysis_custom", "")

        if chat_text != preset.get("chat", ""):
            cfg.set("prompts", "chat_custom", chat_text)
        else:
            cfg.set("prompts", "chat_custom", "")

        # 지식 관리 — 체크된 파일 목록
        enabled = []
        for i in range(self._knowledge_list.count()):
            item = self._knowledge_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                enabled.append(item.text())
        cfg.set("knowledge", "enabled_files", enabled)

        # 음성
        cfg.set("audio", "enabled", self._audio_enabled.isChecked())
        cfg.set("audio", "volume", self._volume_slider.value())

        # 외형
        cfg.set("appearance", "theme", self._theme_combo.currentData())
        cfg.set("appearance", "default_opacity", self._opacity_slider.value())
        cfg.set("appearance", "base_font_size", self._font_size.value())

        cfg.save()
        logger.info("사용자 설정 저장 완료")

        # 스타일 즉시 반영
        self._apply_style()
        self.settings_saved.emit()

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_style()
        self._load_to_ui()
