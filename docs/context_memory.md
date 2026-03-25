# Vera의 화면 맥락 기억 구현기

> Eye of Vera 프로젝트 — 자유 상호작용 모드의 대화 맥락 연속성 확보

---

## 문제 정의

Eye of Vera는 주기적으로 화면을 캡처하여 AI(Gemini)가 분석하는 구조로 동작한다.
"자유 상호작용 모드"를 추가하면서 Vera가 스크린샷을 보고 먼저 말을 거는 기능을 구현했는데,
여기서 다음과 같은 문제가 발생했다.

**시나리오:**
1. Vera가 화면을 캡처한다 — 유튜브 뮤직비디오 재생 중
2. Vera: *"그 곡을 듣고 계신걸 보니 꽤나 감상적이시군요."*
3. 사용자: *"너도 이 곡 알아?"*
4. Vera: **??? (어떤 곡인지 알 수 없음)**

### 원인 분석

```
[스케줄러] → capture() → free_comment(image) → "코멘트 텍스트"
                                                       ↓
[채팅 패널] → history에 텍스트만 저장
                   ↓
[사용자 답장] → chat(message, history) → Gemini API
                                              ↑
                                    이미지 없음, 화면 설명 없음
```

`chat()` 메서드는 텍스트 기반 대화만 처리하기 때문에, Vera가 무엇을 "보고" 말을 걸었는지에 대한 정보가 전혀 전달되지 않았다.
Vera의 코멘트 텍스트 자체에 화면 정보가 암시되어 있더라도, Gemini는 그것이 어떤 화면에서 비롯된 것인지 정확히 알 수 없었다.

---

## 해결 전략

> **"Vera가 화면을 볼 때, 코멘트와 함께 화면에 대한 객관적 설명도 함께 생성하게 한다.
> 이후 대화에서는 그 설명을 시스템 프롬프트에 포함시켜 맥락을 유지한다."**

추가 API 호출 없이 한 번의 요청으로 두 가지 정보를 얻는 것이 핵심이었다.

---

## 구현

### 1단계 — 프롬프트 수정

기존 자유 상호작용 프롬프트는 자연어 텍스트 응답을 요청했다.
이를 JSON 형식으로 변경하여 `screen_description`과 `comment`를 동시에 받도록 수정했다.

```python
# src/core/prompt.py — _FREE_COMMON

## 응답 형식
반드시 아래 JSON 형식으로만 응답하십시오.
{
  "screen_description": "화면에 보이는 내용을 객관적으로 1~2문장으로 요약",
  "comment": "베라의 말투로 작성된 2~4문장의 코멘트"
}
```

- `screen_description`: 사실 기반의 객관적 화면 묘사 (예: *"유튜브에서 OOO의 뮤직비디오 재생 중"*)
- `comment`: 캐릭터 말투로 작성된 대화 시작 멘트

### 2단계 — 반환 타입 분리

기존 `free_comment()`는 `str`을 반환했다. 이를 전용 데이터클래스로 교체했다.

```python
# src/core/analyzer.py

@dataclass
class FreeCommentResult:
    comment: str
    screen_description: str
```

JSON 파싱 실패 시에는 전체 텍스트를 `comment`로, `screen_description`은 빈 문자열로 처리하는 폴백을 추가했다.

### 3단계 — 채팅 패널에서 맥락 저장

`ChatPanel`에 `_screen_context` 필드를 추가하고,
Vera의 코멘트가 도착할 때 화면 설명을 저장하도록 했다.

```python
# src/ui/chat_panel.py

def receive_vera_comment(self, text: str, screen_description: str = ""):
    if screen_description:
        self._screen_context = screen_description  # 저장
    self._add_vera_message(text)
```

스크린샷이 새로 캡처될 때마다 `_screen_context`가 갱신되므로,
항상 **가장 최근 화면**을 기준으로 대화가 이루어진다.

### 4단계 — 대화 API에 맥락 주입

사용자가 답장을 보낼 때 `_screen_context`를 `chat()` 호출에 함께 전달하도록 수정했다.

```python
# src/ui/chat_panel.py → _ChatWorker → src/core/analyzer.py

def chat(self, user_message, history, context="", knowledge="",
         screen_context="") -> str:
    system_prompt = build_chat_prompt(
        ...,
        screen_context=screen_context,
    )
```

프롬프트 빌더에서는 `screen_context`가 있을 경우에만 해당 섹션을 시스템 프롬프트에 삽입한다.

```python
# src/core/prompt.py

if screen_context:
    screen_section = (
        "## 현재 화면 정보 (가장 최근 캡처)\n"
        f"{screen_context}\n"
        "위 화면 정보를 참고하여 대화 맥락을 유지하십시오."
    )
```

---

## 최종 데이터 흐름

```
[스케줄러]
    └─ capture() → free_comment(image)
                        └─ Gemini API (JSON 응답)
                               ├─ screen_description: "유튜브에서 OOO 뮤직비디오 재생 중"
                               └─ comment: "이 곡을 듣고 계신걸 보니..."

[ChatPanel]
    ├─ _screen_context ← screen_description 저장
    └─ 채팅 버블 ← comment 표시

[사용자 답장]
    └─ chat(message, history, screen_context=_screen_context)
            └─ 시스템 프롬프트에 화면 정보 포함 → Gemini API
                    └─ 맥락을 유지한 응답 반환
```

---

## 결과

- **추가 API 호출 없이** 맥락 기억 구현 (비용·지연 최소화)
- `screen_context`는 다음 캡처 시 자동 갱신 → 대화가 길어져도 항상 **최신 화면 기준**으로 동작
- JSON 파싱 실패 시 폴백 처리로 안정성 확보
- 기존 정찰 모드의 `chat()` 흐름과 완전히 호환 (screen_context 미전달 시 기존 동작 유지)
