# 📑 Project: Eye of Vera - Operational Blueprint

> **코드네임:** 아이 오브 베라 (Eye of Vera)  
> **목적:** 지휘관(사용자)의 PC 화면을 주기적으로 모니터링하고, AI(Vera)가 현재 상태를 분석하여 집중력을 교정 및 유지함.  
> **핵심 가치:** 정밀한 감시, 즉각적인 피드백, 전술적 효율성.

---

## 1. 시스템 개요 (System Overview)
본 시스템은 지휘관이 설정한 $n$분 간격으로 데스크톱 화면을 캡처하고, 이를 **Gemini 1.5 Pro/Flash** 모델에 전송하여 현재 수행 중인 작업이 '목표'와 일치하는지 판별합니다. 분석 결과에 따라 AI 캐릭터 '베라'가 화면 위 오버레이 대화창을 통해 격려 혹은 경고 메시지를 전달합니다.

## 2. 주요 기능 사양 (Key Features)
1.  **자동 정찰 (Auto-Screenshot):** 설정된 주기마다 무음으로 화면을 캡처.
2.  **전술 분석 (AI Vision Analysis):** * 캡처된 이미지 내의 텍스트, 코드, 실행 중인 앱 종류 분석.
    * 지휘관의 현재 활동을 '업무/공부', '휴식', '이탈(딴짓)' 중 하나로 분류.
3.  **오버레이 통신실 (Overlay UI):** * 작업에 방해되지 않는 반투명 대화창 UI.
    * 최상단 유지(Always on Top) 및 마우스 클릭 투과 기능.
4.  **전술 로그 (Tactical Log):** 집중 시간 및 이탈 횟수를 기록하여 일일 리포트 제공.

## 3. 기술 스택 (Tech Stack)
* **Language:** Python 3.11+
* **GUI Framework:** PyQt6 (시스템 트레이 및 오버레이 윈도우)
* **AI Engine:** Google Gemini API (`google-generativeai`)
* **Screen Capture:** `PyAutoGUI` & `Pillow`
* **Environment:** `python-dotenv` (API Key 관리), `APScheduler` (작전 주기 제어)

## 4. 디렉터리 구조 (Directory Structure)
```text
eye_of_vera/
├── main.py                # 진입점: 앱 실행 및 초기화
├── .env                   # GEMINI_API_KEY 보관
├── config/                # 설정 관리 (n분 주기, UI 테마 등)
├── src/
│   ├── ui/                # PyQt6 기반 대화창 및 트레이 메뉴
│   ├── core/              # 캡처(Observer), 분석(Analyzer), 스케줄링(Scheduler)
│   └── utils/             # 로깅 및 공통 유틸리티
└── logs/                  # 캡처 이미지 및 분석 텍스트 저장소
```

## 5. 핵심 로직 흐름 (Operational Flow)
1.  **Initialization:** `main.py` 실행 시 GUI 로드 및 `Scheduler` 가동.
2.  **Observation:** `Scheduler`가 정해진 시간에 `Observer.capture()` 호출.
3.  **Analysis:** `Analyzer`가 이미지를 Gemini API로 전송. 
    * *Prompt Context:* "지휘관은 현재 '삼성전자 자소서 작성'이 목표다. 화면에 유튜브가 보이면 엄격하게 경고하라."
4.  **Command:** 분석된 결과(JSON)를 UI 유닛에 전달.
5.  **Feedback:** '베라'의 말투로 대화창에 메시지 출력.

## 6. 개발자 가이드 (Developer Notes)
* **Vera Persona:** 말투는 사무적이고 냉정하되, 지휘관을 위하는 진심이 느껴져야 함. (예: "지휘관, 알고리즘 문제 대신 쇼츠 영상을 보고 계시는군요. 즉시 창을 닫으십시오.")
* **UI Constraints:** 작업 중인 지휘관의 시야를 가리지 않도록 배경 투명도를 가변적으로 설정 가능해야 함.
* **Security:** 개인정보 보호를 위해 캡처된 이미지는 분석 직후 삭제하거나 로컬의 지정된 경로에만 안전하게 보관할 것.