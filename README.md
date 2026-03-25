# Eye of Vera

An AI-powered focus assistant that monitors your desktop activity and provides real-time feedback to help you stay on track.

Vera periodically captures your screen, analyzes what you're doing with Google Gemini, and delivers feedback through a non-intrusive overlay window — keeping you accountable without breaking your flow.

---

## Features

- **Periodic Screen Analysis** — Captures your screen at a configurable interval and sends it to the Gemini API for analysis.
- **Focus Classification** — Categorizes your current activity as `FOCUS`, `RELAX`, or `DEVIATION` based on a goal you define.
- **Overlay UI** — A translucent, always-on-top chat window delivers Vera's feedback directly on your screen. Click-through enabled so it never blocks your work.
- **Chat Mode** — Have a conversation with Vera at any time. She references your session data and recent screen context to give grounded, relevant responses.
- **Free Interaction Mode** — Vera can comment freely on what she sees on your screen — no judgment, just conversation.
- **Persona System** — Choose from multiple built-in AI personas (default, friendly, strict) or write your own custom prompt.
- **Break Reminders** — Optional Pomodoro-style reminders (50 min focus / 10 min break).
- **Activity Log & Reports** — Session history is stored locally in SQLite. View daily focus reports from the tray menu.

## Tech Stack

| Layer | Library |
|---|---|
| GUI | PyQt6 |
| AI Engine | Google Gemini API (`google-generativeai`) |
| Screen Capture | PyAutoGUI, Pillow |
| Scheduler | APScheduler |
| Storage | SQLite (`logs/vera.db`) |
| Config | python-dotenv |

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

Key settings in `.env`:

| Variable | Default | Description |
|---|---|---|
| `CAPTURE_INTERVAL_MINUTES` | `5` | How often Vera checks your screen |
| `OVERLAY_OPACITY` | `0.9` | Overlay transparency (0.0–1.0) |
| `KEEP_SCREENSHOTS` | `false` | Whether to retain captured images after analysis |
| `BREAK_TIME_REMINDER` | `true` | Enable Pomodoro-style break reminders |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Project Structure

```
eye_of_vera/
├── main.py               # Entry point
├── config/               # Settings and user config management
├── src/
│   ├── core/             # Observer, Analyzer, Scheduler, Prompt engine
│   ├── ui/               # Overlay window, tray menu, settings/log panels
│   └── utils/            # Logger and helpers
└── logs/                 # SQLite database and optional screenshot storage
```

## Privacy

By default, screenshots are deleted immediately after analysis and never leave your machine beyond the Gemini API call. Set `KEEP_SCREENSHOTS=true` in `.env` only if you want to retain them locally for review.

## Requirements

- Python 3.11+
- A valid [Google Gemini API key](https://aistudio.google.com/app/apikey)
- Windows (overlay and tray features are tested on Windows 10/11)
