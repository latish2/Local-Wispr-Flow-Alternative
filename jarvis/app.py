from __future__ import annotations

import logging
import sys
import threading
from pathlib import Path

from PySide6.QtCore import QLockFile, QObject, QUrl, Signal, Slot
from PySide6.QtGui import QAction, QDesktopServices, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from . import __version__
from .cleanup import ollama_cleanup, remove_fillers
from .config import Config, data_dir
from .history import History
from .hotkey import HotkeyListener, display_hotkey
from .inserter import insert_text
from .recorder import Recorder
from .transcriber import Transcriber
from .ui.dialogs import HistoryDialog, SettingsDialog
from .ui.overlay import Overlay

log = logging.getLogger("jarvis")


def asset(name: str) -> str:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return str(base / "assets" / name)


def beep(freq: int) -> None:
    if sys.platform == "win32":
        import winsound

        threading.Thread(target=winsound.Beep, args=(freq, 70), daemon=True).start()


class Controller(QObject):
    hotkey_down = Signal()
    hotkey_up = Signal()
    hotkey_cancel = Signal()
    level = Signal(float)
    model_ready = Signal(str)
    model_failed = Signal(str)
    finished = Signal(str, str)
    failed = Signal(str)

    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        self.cfg = Config.load()
        self.history = History(limit=self.cfg.history_size)
        self.transcriber = Transcriber(self.cfg)
        self.overlay = Overlay()
        self.recorder: Recorder | None = None
        self.listener: HotkeyListener | None = None
        self.state = "loading"  # loading | idle | recording | busy | error
        self.status = "Loading speech model…"

        self.hotkey_down.connect(self._on_down)
        self.hotkey_up.connect(self._on_up)
        self.hotkey_cancel.connect(self._on_cancel)
        self.level.connect(self.overlay.push_level)
        self.model_ready.connect(self._on_model_ready)
        self.model_failed.connect(self._on_model_failed)
        self.finished.connect(self._on_finished)
        self.failed.connect(self._on_failed)

        self._build_tray()
        self._start_listener()
        self._load_model()

    # ---- setup -------------------------------------------------------------
    def _build_tray(self) -> None:
        self.tray = QSystemTrayIcon(QIcon(asset("jarvis.png")), self.app)
        menu = QMenu()
        self.status_action = QAction(self.status, menu)
        self.status_action.setEnabled(False)
        menu.addAction(self.status_action)
        menu.addSeparator()
        menu.addAction("Settings…", self.open_settings)
        menu.addAction("History…", self.open_history)
        menu.addAction("Open data folder", lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(data_dir()))))
        menu.addSeparator()
        menu.addAction("Quit Jarvis", self.quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(
            lambda reason: self.open_settings() if reason == QSystemTrayIcon.DoubleClick else None
        )
        self._menu = menu
        self.tray.show()
        self._set_status(self.status)

    def _set_status(self, text: str) -> None:
        self.status = text
        self.status_action.setText(text)
        self.tray.setToolTip(f"Jarvis — {text}"[:127])

    def _start_listener(self) -> None:
        if self.listener:
            self.listener.stop()
        self.listener = HotkeyListener(
            self.cfg.hotkey, self.hotkey_down.emit, self.hotkey_up.emit, self.hotkey_cancel.emit
        )
        self.listener.start()

    def _load_model(self) -> None:
        self.state = "loading"
        self._set_status("Loading speech model… (first run downloads it)")

        def work():
            try:
                self.model_ready.emit(self.transcriber.load())
            except Exception as e:  # noqa: BLE001
                log.exception("model load failed")
                self.model_failed.emit(str(e))

        threading.Thread(target=work, daemon=True).start()

    def _ready_text(self, desc: str) -> str:
        verb = "Hold" if self.cfg.mode == "hold" else "Press"
        return f"Ready ({desc}) — {verb} {display_hotkey(self.cfg.hotkey)} to dictate"

    @Slot(str)
    def _on_model_ready(self, desc: str) -> None:
        self.state = "idle"
        self._set_status(self._ready_text(desc))
        verb = "Hold" if self.cfg.mode == "hold" else "Press"
        self.tray.showMessage(
            "Jarvis is ready", f"{verb} {display_hotkey(self.cfg.hotkey)} and speak. Esc cancels.",
            QSystemTrayIcon.Information, 4000,
        )

    @Slot(str)
    def _on_model_failed(self, err: str) -> None:
        self.state = "error"
        self._set_status("Model failed to load — see Settings / log")
        self.tray.showMessage("Jarvis: model failed to load", err[:200], QSystemTrayIcon.Critical, 8000)

    # ---- hotkey handling ---------------------------------------------------
    @Slot()
    def _on_down(self) -> None:
        if self.cfg.mode == "toggle" and self.state == "recording":
            self._stop_recording()
        elif self.state == "idle":
            self._start_recording()
        elif self.state == "loading":
            self.overlay.flash("Speech model is still loading…")
        elif self.state == "error":
            self.overlay.flash("Model failed to load — check Settings")

    @Slot()
    def _on_up(self) -> None:
        if self.cfg.mode == "hold" and self.state == "recording":
            self._stop_recording()

    @Slot()
    def _on_cancel(self) -> None:
        if self.state == "recording" and self.recorder:
            self.recorder.stop()
            self.state = "idle"
            self.overlay.flash("Cancelled", 900)

    def _start_recording(self) -> None:
        self.recorder = Recorder(self.cfg.input_device, on_level=self.level.emit)
        try:
            self.recorder.start()
        except Exception as e:  # noqa: BLE001
            log.exception("mic start failed")
            self.overlay.flash(f"Microphone error: {e}"[:80], 4000)
            return
        self.state = "recording"
        if self.cfg.sounds:
            beep(880)
        self.overlay.listening()

    def _stop_recording(self) -> None:
        audio = self.recorder.stop() if self.recorder else None
        self.state = "busy"
        if self.cfg.sounds:
            beep(620)
        self.overlay.processing()
        threading.Thread(target=self._process, args=(audio,), daemon=True).start()

    def _process(self, audio) -> None:
        try:
            raw = self.transcriber.transcribe(audio) if audio is not None else ""
            text = remove_fillers(raw) if self.cfg.remove_fillers else raw
            if text and self.cfg.cleanup_enabled:
                text = ollama_cleanup(text, self.cfg.ollama_url, self.cfg.ollama_model)
            if text:
                self.listener.wait_released()
                insert_text(text + " ", self.cfg.restore_clipboard)
            self.finished.emit(text, raw)
        except Exception as e:  # noqa: BLE001
            log.exception("transcription failed")
            self.failed.emit(str(e))

    @Slot(str, str)
    def _on_finished(self, text: str, raw: str) -> None:
        self.state = "idle"
        if text:
            self.history.add(text, raw)
            self.overlay.idle()
        else:
            self.overlay.flash("Didn't catch that", 1200)

    @Slot(str)
    def _on_failed(self, err: str) -> None:
        self.state = "idle"
        self.overlay.flash(f"Error: {err}"[:80], 4000)

    # ---- menu actions ------------------------------------------------------
    def open_settings(self) -> None:
        before = (self.cfg.model, self.cfg.device)
        if SettingsDialog(self.cfg, self.status).exec():
            self.history.limit = self.cfg.history_size
            self._start_listener()
            if (self.cfg.model, self.cfg.device) != before or self.state == "error":
                self._load_model()
            elif self.state == "idle":
                where = "GPU" if self.transcriber.device == "cuda" else "CPU"
                self._set_status(self._ready_text(f"{self.transcriber.model_name} on {where}"))

    def open_history(self) -> None:
        HistoryDialog(self.history).exec()

    def quit(self) -> None:
        if self.listener:
            self.listener.stop()
        self.tray.hide()
        self.app.quit()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.FileHandler(data_dir() / "jarvis.log", encoding="utf-8"), logging.StreamHandler()],
    )
    log.info("Jarvis %s starting", __version__)
    if sys.platform == "win32":
        # Own taskbar identity so Windows shows our icon instead of python's.
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Jarvis.Dictation")

    app = QApplication(sys.argv)
    app.setApplicationName("Jarvis")
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(QIcon(asset("jarvis.png")))

    lock = QLockFile(str(data_dir() / "jarvis.lock"))
    if not lock.tryLock(100):
        QMessageBox.information(None, "Jarvis", "Jarvis is already running (check the system tray).")
        return
    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.warning(None, "Jarvis", "No system tray available.")

    controller = Controller(app)  # noqa: F841 - keep a reference alive
    sys.exit(app.exec())
