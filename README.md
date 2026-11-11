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

## Install on Windows (step by step)

### Requirements

- Windows 10 or 11 (64-bit)
- Internet connection for the one-time setup. After that, Jarvis works fully offline.
- **Disk space:** ~5 GB with an NVIDIA GPU, or ~1.5 GB CPU-only

| Part | Size |
| --- | --- |
| Python 3.12 | ~100 MB |
| App dependencies (Qt UI, Whisper engine, audio) | ~1.1 GB |
| NVIDIA CUDA libraries (installed only if you have an NVIDIA GPU) | ~1.5–2 GB |
| Speech model `large-v3-turbo` (GPU default, downloaded on first launch) | ~1.6 GB |
| Optional: Ollama + `llama3.2:3b` for AI cleanup | ~3 GB |

### Step 1: Install Python 3.12

1. Open <https://www.python.org/downloads/windows/> and download the **Windows installer (64-bit)** for the latest **Python 3.12.x**.
2. Run the installer and **tick "Add python.exe to PATH"** at the bottom of the first screen, then click **Install Now**.
3. Check that it worked: open **Command Prompt** (press `Win`, type `cmd`, press Enter) and run:
   ```bat
   py -3.12 --version
   ```
   It should print `Python 3.12.x`.

> Use 3.12. Newer versions (3.13 or later) may not yet have all the required packages.

### Step 2: Update your NVIDIA driver (GPU users)

Install the latest **Game Ready** or **Studio** driver from <https://www.nvidia.com/Download/index.aspx> or through the GeForce Experience / NVIDIA App.
To check, run `nvidia-smi` in Command Prompt; it should list your GPU.
You do **not** need to install the CUDA Toolkit. `setup.bat` installs the required CUDA libraries inside the project folder.

### Step 3: Download Jarvis

Choose **either** option:

- **Option A: ZIP (no Git needed).** On the GitHub repo page, click **Code → Download ZIP**. Right-click the ZIP → **Extract All…** and extract it somewhere simple, such as `C:\Jarvis`.
- **Option B: Git.**
  ```bat
  git clone https://github.com/latish2/Jarvis.git C:\Jarvis
  ```

> Avoid folders synced by OneDrive (such as `Desktop` or `Documents`), because syncing large model files can slow things down or cause errors.

### Step 4: Run the setup (one time)

1. Open the Jarvis folder in File Explorer.
2. Double-click **`setup.bat`**. If Windows SmartScreen shows a warning, click **More info → Run anyway**.
3. Wait 5–15 minutes, depending on your internet speed. The script:
   - creates a private Python environment in `.venv`
   - installs the app's dependencies
   - detects your NVIDIA GPU and installs the CUDA libraries
4. When it prints **"Setup complete"**, close the window.

### Step 5: Start Jarvis

1. Double-click **`run.bat`**. No window opens. Instead, a **Jarvis icon** (purple waveform) appears in the system tray at the bottom-right of the taskbar. If you don't see it, click the **^** arrow.
2. **First launch only:** Jarvis downloads the speech model (~1.6 GB) to `%APPDATA%\Jarvis\models`. This takes a few minutes. Hover over the tray icon to see the status. When the model is ready, you'll get a **"Jarvis is ready"** notification.

### Step 6: Dictate

1. Click into any text box, such as Notepad, a browser, Word, or WhatsApp Desktop.
2. **Hold `Ctrl` + `Win`**, speak, then **release**.
3. A small waveform appears while you speak. After you release, the text is typed in for you.
4. Press `Esc` while recording to cancel.

The first time you record, Windows may ask for microphone access. Allow it under **Settings → Privacy & security → Microphone → "Let desktop apps access your microphone"**.

### Step 7 (optional): Start Jarvis automatically

Right-click the tray icon → **Settings…** → tick **"Start Jarvis when I log in"** → **Save**.
You can also pin `run.bat` by right-clicking it → **Send to → Desktop (create shortcut)**.

### Updating

- **ZIP:** download the new ZIP and extract it over the old folder.
- **Git:** run `git pull` in the folder.

In both cases, run `setup.bat` again afterwards. Your settings and models in `%APPDATA%\Jarvis` are kept.

### Uninstalling

1. Right-click the tray icon → **Quit Jarvis**.
2. If you enabled auto-start, untick it in Settings first.
3. Delete the Jarvis folder (for example `C:\Jarvis`) and `%APPDATA%\Jarvis` (paste that path into the File Explorer address bar).

### Troubleshooting

| Problem | Fix |
| --- | --- |
| `setup.bat` says Python isn't found | Reinstall Python 3.12 and tick "Add python.exe to PATH", then reopen the folder |
| Nothing happens when I run `run.bat` | Run **`run-debug.bat`** instead. It shows a console with the error. Logs are also saved to `%APPDATA%\Jarvis\jarvis.log` |
| Status says "on CPU" even though I have an NVIDIA GPU | Update the NVIDIA driver, run `setup.bat` again, and make sure Settings → Compute device is `auto` or `cuda` |
| "Didn't catch that" | Check that the right microphone is selected in Settings → Microphone, and in Windows microphone privacy settings |
| Text isn't typed into an app that runs as Administrator | Windows blocks this. Run Jarvis as Administrator too, or use a non-admin app |
| `Ctrl+Win` conflicts with another shortcut | Choose another hotkey in Settings, such as `ctrl+alt` or `f9` |
| GPU out of memory | Choose a smaller model (`small` or `distil-large-v3`) in Settings |
| The model download failed or got stuck | Delete `%APPDATA%\Jarvis\models` and restart Jarvis |

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
