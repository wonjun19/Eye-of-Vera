# Eye of Vera

[English](README.md)

AI 기반 집중력 보조 도우미 — 데스크탑 화면을 주기적으로 분석하고, 실시간 피드백으로 목표에 집중할 수 있도록 돕습니다.

Vera는 설정한 간격마다 화면을 캡처하여 Google Gemini에 전송하고, 비침습적인 오버레이 창을 통해 피드백을 전달합니다. 작업 흐름을 방해하지 않으면서 자신을 객관적으로 바라볼 수 있게 해줍니다.

---

## 주요 기능

- **주기적 화면 분석** — 설정한 간격마다 화면을 캡처하여 Gemini API로 분석합니다.
- **집중 상태 분류** — 현재 활동을 목표에 따라 `FOCUS`(집중) · `RELAX`(휴식) · `DEVIATION`(이탈) 세 상태로 분류합니다.
- **오버레이 UI** — 반투명 항상-위 채팅창으로 피드백을 전달합니다. 클릭-스루 지원으로 작업을 절대 가리지 않습니다.
- **채팅 모드** — 언제든지 Vera와 대화할 수 있습니다. 세션 데이터와 최근 화면 컨텍스트를 기반으로 근거 있는 답변을 제공합니다.
- **자유 상호작용 모드** — Vera가 화면에 보이는 것들에 대해 자유롭게 말을 걸어옵니다. 판단이 아닌 대화 중심의 모드입니다.
- **음성 대사** — 집중 상태가 변할 때 Vera의 음성이 재생됩니다. `FOCUS`(집중)와 `DEVIATION`(이탈) 상태에서만 재생되며, `RELAX`(휴식) 상태에서는 무음입니다.
- **프롬프트 프리셋** — 기본·친근·엄격 등 내장 프리셋 중에서 선택하거나, 분석 프롬프트와 채팅 프롬프트를 직접 편집할 수 있습니다.
- **지식 관리** — 마크다운 또는 텍스트 파일을 Vera의 컨텍스트에 추가할 수 있습니다. 설정 패널에서 태그를 지정하고 파일별로 활성화/비활성화할 수 있습니다.
- **설정 패널** — 정찰 설정·프롬프트 편집·지식 관리·음성·외형을 5개 탭으로 관리하는 앱 내 설정 UI입니다. 설정 파일을 직접 수정할 필요가 없습니다.
- **테마 시스템** — 여러 가지 내장 색상 테마를 제공합니다. 재시작 없이 전환할 수 있습니다.
- **휴식 알림** — 뽀모도로 방식의 휴식 알림 (집중/휴식 시간 개별 설정 가능).
- **활동 로그 & 리포트** — 세션 기록이 로컬 SQLite에 저장됩니다. 트레이 메뉴에서 일별 집중 리포트를 확인할 수 있습니다.

## 기술 스택

| 계층 | 라이브러리 |
|---|---|
| GUI | PyQt6 |
| 오디오 | PyQt6.QtMultimedia |
| AI 엔진 | Google Gemini API (`google-genai`) |
| 화면 캡처 | PyAutoGUI, Pillow |
| 스케줄러 | APScheduler |
| 저장소 | SQLite (`logs/vera.db`) |
| 설정 | python-dotenv, JSON (`config/user_config.json`) |

## 시작하기

### 1. 클론 및 의존성 설치

```bash
git clone https://github.com/your-username/eye-of-vera.git
cd eye-of-vera
pip install -r requirements.txt
```

### 2. API 키 설정

`.env.example`을 `.env`로 복사한 뒤 Gemini API 키를 입력합니다:

```bash
cp .env.example .env
```

```env
GEMINI_API_KEY=your_api_key_here
```

### 3. 실행

```bash
python main.py
```

Vera가 시스템 트레이에 나타납니다. 트레이 아이콘을 우클릭하여 목표를 설정하고 세션을 시작하세요.

## 설정

API 키와 일부 저수준 옵션은 `.env`에서 관리합니다:

| 변수 | 기본값 | 설명 |
|---|---|---|
| `GEMINI_API_KEY` | — | Google Gemini API 키 (필수) |
| `LOG_LEVEL` | `INFO` | 로그 상세 수준 |

그 외 모든 설정(캡처 간격, 테마, 음성, 프롬프트, 지식 파일, 휴식 알림 등)은 앱 내 **설정 패널**에서 관리합니다. 트레이 아이콘 우클릭 후 **설정**을 선택하세요.

## 프로젝트 구조

```
eye_of_vera/
├── main.py                    # 진입점
├── requirements.txt
├── .env.example
├── config/                    # 앱 설정 및 사용자 설정 관리
│   ├── settings.py            # .env 로더 및 앱 기본값
│   └── user_config.py         # JSON 기반 사용자 환경설정 (UserConfig)
├── src/
│   ├── core/
│   │   ├── analyzer.py        # Gemini API 호출 및 응답 파싱
│   │   ├── audio.py           # 상태 기반 음성 대사 플레이어
│   │   ├── database.py        # SQLite 세션 로깅
│   │   ├── knowledge.py       # 지식 파일 로더 및 태그 관리자
│   │   ├── observer.py        # 오케스트레이터 (핵심 컴포넌트 총괄)
│   │   ├── prompt.py          # 프롬프트 프리셋 및 템플릿 엔진
│   │   └── scheduler.py       # APScheduler 래퍼
│   └── ui/
│       ├── chat_window.py     # 메인 오버레이 채팅창
│       ├── chat_panel.py      # 채팅 메시지 렌더링
│       ├── design.py          # VERA-OS 디자인 시스템 (토큰, 테마 팔레트)
│       ├── log_panel.py       # 세션 로그 뷰어
│       ├── report_window.py   # 일별 집중 리포트 창
│       ├── settings_panel.py  # 설정 UI (5개 탭)
│       └── tray_menu.py       # 시스템 트레이 아이콘 및 메뉴
├── assets/
│   ├── icons/                 # 앱 아이콘 (.ico / .png)
│   └── Dialogue preset/       # 음성 대사 MP3 파일
├── knowledge/                 # 사용자 제공 지식 파일 (.md / .txt)
└── logs/                      # SQLite DB 및 선택적 스크린샷 저장소
```

## 개인정보 보호

기본적으로 스크린샷은 분석 직후 삭제되며, Gemini API 전송 외에는 외부로 전달되지 않습니다. 로컬에 저장하려면 설정 패널에서 **스크린샷 보관** 옵션을 활성화하세요.

## 요구사항

- Python 3.10+
- 유효한 [Google Gemini API 키](https://aistudio.google.com/app/apikey)
- Windows (오버레이 및 트레이 기능은 Windows 10/11에서 테스트됨)
