<p align="center"><img src="assets/jarvis-512.png" width="128" alt="Jarvis logo"></p>

# Jarvis — free, fully local voice dictation

Hold a hotkey, speak, release: your words are typed into whatever app has focus (browser, Word, Slack, VS Code, …).
Speech recognition runs **100% on your machine** with [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (OpenAI Whisper models). No account, no API keys, no subscription; your audio never leaves your PC.

## Features

- **Push-to-talk anywhere**: hold `Ctrl+Win` (configurable), or use toggle mode. `Esc` cancels.
- **GPU accelerated** on NVIDIA cards (uses `large-v3-turbo`), with automatic CPU fallback (`base`).
- **99 languages** with auto-detect, including English, Hindi, and Hinglish-style mixed speech.
- **Custom vocabulary** for names and jargon so Whisper spells them right.
- **Filler-word removal** (um, uh) built in.
- **Optional AI polish**: fixes punctuation, removes false starts, and applies "no wait, I meant…" corrections, using a local LLM through [Ollama](https://ollama.com). Free and offline too.
- Floating waveform overlay, tray menu, history of everything you dictated, and launch at login.

## Install (Windows)

1. Install **Python 3.12** from [python.org](https://www.python.org/downloads/windows/) and tick **"Add python.exe to PATH"**.
2. Download or clone this repo, then double-click **`setup.bat`**. It creates `.venv`, installs dependencies, and, if it finds an NVIDIA GPU, installs the CUDA libraries into the venv. You don't need a system-wide CUDA toolkit, just a recent NVIDIA driver.
3. Double-click **`run.bat`**. A Jarvis icon appears in the system tray. The first launch downloads the speech model (~1.6 GB for `large-v3-turbo`) to `%APPDATA%\Jarvis\models`.
4. Click into any text box, **hold `Ctrl+Win`, speak, release.**

If something doesn't work, run **`run-debug.bat`** to see logs. Logs are also saved to `%APPDATA%\Jarvis\jarvis.log`.

### Recommended settings for an RTX 3050 (4 GB)

The defaults (`auto` model and `auto` device) pick `large-v3-turbo` with `int8_float16` on the GPU, which uses about 1.5 GB of VRAM and typically transcribes a 10-second clip in well under a second.
If you also run Ollama on the GPU and memory gets tight, switch the model to `small` or `distil-large-v3` in Settings.

### Optional: AI cleanup with Ollama

1. Install [Ollama](https://ollama.com/download) and run `ollama pull llama3.2:3b`. Alternatives: `qwen2.5:3b`, or `llama3.2:1b` for more speed.
2. Tray icon → **Settings** → tick **"Polish text with a local LLM"**.

If Ollama isn't running, Jarvis simply types the raw transcript.

### Build a standalone .exe (optional)

Run `build.bat` to produce `dist\Jarvis\Jarvis.exe`, which you can copy anywhere without Python. With GPU libraries included it is large (~1–2 GB).

## Usage tips

| Action | How |
| --- | --- |
| Dictate | Hold the hotkey, speak, release |
| Cancel | Press `Esc` while recording |
| Change hotkey/mode/model | Tray icon → Settings (or double-click the tray icon) |
| Recover past text | Tray icon → History (double-click an entry to copy it) |

Hotkey examples: `ctrl+win`, `ctrl+alt`, `ctrl+shift+space`, `f9`, `alt_r`.

## How it works

```
hotkey (pynput) → mic capture 16 kHz (sounddevice) → faster-whisper (+VAD) → filler removal
  → [optional Ollama polish] → clipboard + Ctrl+V into the focused app → clipboard restored
```

| Module | Role |
| --- | --- |
| `jarvis/app.py` | Tray app and state machine |
| `jarvis/hotkey.py` | Global hold/toggle hotkey |
| `jarvis/recorder.py` | Microphone capture |
| `jarvis/transcriber.py` | Whisper model loading (GPU→CPU fallback) |
| `jarvis/cleanup.py` | Text cleanup |
| `jarvis/inserter.py` | Pastes the text |
| `jarvis/ui/` | Overlay and dialogs |

## Development

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/python -m pytest
python tools/make_icon.py   # regenerate the logo/icons
```

Jarvis also runs on macOS and Linux (X11). On macOS, grant Accessibility and Microphone permissions; use `cmd` in the hotkey.

## License

MIT. Jarvis is an independent, original project and is not affiliated with Wispr or Wispr Flow.
