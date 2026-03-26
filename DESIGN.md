# VERA-OS Design System

## Overview

VERA-OS UI는 군사 작전 지휘 시스템을 모티프로 한 어두운 테마 기반 데스크탑 UI입니다.
모든 디자인 토큰은 `src/ui/design.py`에서 PyQt6 구현체로 관리됩니다.

---

## Color Tokens

### Status Colors

| Status    | Background   | Background 2 | Border   | Accent   | Text     |
|-----------|-------------|--------------|----------|----------|----------|
| FOCUS     | `#0c1e10`   | `#172c1c`    | `#43a047`| `#66bb6a`| `#c8e6c9`|
| RELAX     | `#0c1224`   | `#16203c`    | `#5c6bc0`| `#7986cb`| `#c5cae9`|
| DEVIATION | `#200c0c`   | `#301414`    | `#e53935`| `#ef5350`| `#ffcdd2`|
| UNKNOWN   | `#12121e`   | `#1a1a2e`    | `#616161`| `#757575`| `#bdbdbd`|

### Theme Palettes

| Token        | Dark (default) | Military      | Navy      |
|-------------|---------------|---------------|-----------|
| `bg`        | `#1a1a2e`     | `#1a2e1a`     | `#0d1b2a` |
| `border`    | `#5c6bc0`     | `#4caf50`     | `#1b9aaa` |
| `text`      | `#e0e0e0`     | `#c8e6c9`     | `#d4e4f7` |
| `accent`    | `#7986cb`     | `#66bb6a`     | `#4dd0e1` |
| `input_bg`  | `#16162a`     | `#162a16`     | `#0a1628` |

---

## Typography

| Token       | Family              | Size |
|-------------|---------------------|------|
| `FONT_MONO` | Consolas            | –    |
| `FONT_UI`   | 맑은 고딕           | –    |
| `text-xs`   | –                   | 8pt  |
| `text-sm`   | –                   | 9pt  |
| `text-base` | –                   | 10pt |
| `text-md`   | –                   | 11pt |
| `text-lg`   | –                   | 12pt |
| `text-xl`   | –                   | 14pt |

---

## Spacing & Shape

| Token       | Value |
|-------------|-------|
| `radius-sm` | 6px   |
| `radius-md` | 10px  |
| `radius-lg` | 14px  |
| `gap-xs`    | 4px   |
| `gap-sm`    | 8px   |
| `gap-md`    | 12px  |
| `gap-lg`    | 16px  |
| `gap-xl`    | 24px  |

---

## Status Icons

| Status    | Icon |
|-----------|------|
| FOCUS     | `◉`  |
| RELAX     | `◐`  |
| DEVIATION | `⚠`  |
| UNKNOWN   | `○`  |

---

## Animation

| Token            | Value  |
|-----------------|--------|
| `duration-fast`  | 200ms  |
| `duration-normal`| 400ms  |
| `duration-slow`  | 800ms  |
| `pulse-interval` | 30ms   |
| `easing`         | OutQuad|
