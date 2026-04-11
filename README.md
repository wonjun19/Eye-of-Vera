# Eye of Vera

[한국어 문서](README_KO.md)

An AI-powered focus assistant that monitors your desktop activity and provides real-time feedback to help you stay on track.

Vera periodically captures your screen, analyzes what you're doing with Google Gemini, and delivers feedback through a non-intrusive overlay window — keeping you accountable without breaking your flow.

---

## Features

- **Periodic Screen Analysis** — Captures your screen at a configurable interval and sends it to the Gemini API for analysis.
- **Focus Classification** — Categorizes your current activity as `FOCUS`, `RELAX`, or `DEVIATION` based on a goal you define.
- **Overlay UI** — A translucent, always-on-top chat window delivers Vera's feedback directly on your screen. Click-through enabled so it never blocks your work.
- **Chat Mode** — Have a conversation with Vera at any time. She references your session data and recent screen context to give grounded, relevant responses.
- **Free Interaction Mode** — Vera can comment freely on what she sees on your screen — no judgment, just conversation.
- **Voice Dialogue** — Vera plays voiced lines when your focus status changes. Distinct audio cues for `FOCUS` and `DEVIATION` states; silent during `RELAX`.
- **Prompt Presets** — Choose from multiple built-in prompt presets (default, friendly, strict) or write fully custom analysis and chat prompts.
- **Knowledge Management** — Import your own Markdown or text files into Vera's context. Tag and enable/disable files per-session from the Settings panel.
- **Settings Panel** — Full in-app settings UI with tabs for monitoring, prompts, knowledge, audio, and appearance. No manual config file editing required.
- **Theme System** — Multiple built-in color themes; switch without restarting.
- **Break Reminders** — Optional Pomodoro-style reminders (configurable focus / break durations).
- **Activity Log & Reports** — Session history is stored locally in SQLite. View daily focus reports from the tray menu.

## Tech Stack

| Layer | Library |
|---|---|
| GUI | PyQt6 |
| Audio | PyQt6.QtMultimedia |
| AI Engine | Google Gemini API (`google-genai`) |
| Screen Capture | PyAutoGUI, Pillow |
| Scheduler | APScheduler |
| Storage | SQLite (`logs/vera.db`) |
| Config | python-dotenv, JSON (`config/user_config.json`) |

## Getting Started

### 1. Clone and install dependencies

```bash
git clone https://github.com/your-username/eye-of-vera.git
cd eye-of-vera
pip install -r requirements.txt
```

### 2. Set up your API key

Copy `.env.example` to `.env` and fill in your Gemini API key:

```bash
cp .env.example .env
```

```env
GEMINI_API_KEY=your_api_key_here
```

### 3. Run

```bash
python main.py
```

Vera will appear in your system tray. Right-click the tray icon to set your goal and start a session.

## Configuration

The API key and a few low-level options live in `.env`:

| Variable | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | — | Your Google Gemini API key (required) |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

All other settings (capture interval, theme, audio, prompts, knowledge files, break reminders, etc.) are managed through the in-app **Settings Panel** — right-click the tray icon and select **설정**.

## Project Structure

```
eye_of_vera/
├── main.py                    # Entry point
├── requirements.txt
├── .env.example
├── config/                    # Settings and user config management
│   ├── settings.py            # .env loader and app-level defaults
│   └── user_config.py         # JSON-based user preferences (UserConfig)
├── src/
│   ├── core/
│   │   ├── analyzer.py        # Gemini API calls and response parsing
│   │   ├── audio.py           # State-based voice dialogue player
│   │   ├── database.py        # SQLite session logging
│   │   ├── knowledge.py       # Knowledge file loader and tag manager
│   │   ├── observer.py        # Orchestrator (ties all core components together)
│   │   ├── prompt.py          # Prompt presets and template engine
│   │   └── scheduler.py       # APScheduler wrapper
│   └── ui/
│       ├── chat_window.py     # Main overlay chat window
│       ├── chat_panel.py      # Chat message rendering
│       ├── design.py          # VERA-OS design system (tokens, theme palette)
│       ├── log_panel.py       # Session log viewer
│       ├── report_window.py   # Daily focus report window
│       ├── settings_panel.py  # Settings UI (5 tabs)
│       └── tray_menu.py       # System tray icon and menu
├── assets/
│   ├── icons/                 # App icon (.ico / .png)
│   └── Dialogue preset/       # Voice dialogue MP3 files
├── knowledge/                 # User-provided knowledge files (.md / .txt)
└── logs/                      # SQLite database and optional screenshot storage
```

## Privacy

By default, screenshots are deleted immediately after analysis and never leave your machine beyond the Gemini API call. Set `KEEP_SCREENSHOTS` to `true` in the Settings panel only if you want to retain them locally for review.

## Requirements

- Python 3.10+
- A valid [Google Gemini API key](https://aistudio.google.com/app/apikey)
- Windows (overlay and tray features are tested on Windows 10/11)
