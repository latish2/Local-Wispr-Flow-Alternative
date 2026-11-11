from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QPlainTextEdit, QPushButton, QVBoxLayout,
)

from .. import autostart
from ..config import Config
from ..history import History
from ..hotkey import parse_hotkey
from ..recorder import list_input_devices
from ..transcriber import MODELS

LANGUAGES = [("Auto-detect", ""), ("English", "en"), ("Hindi", "hi"), ("Spanish", "es"), ("French", "fr"),
             ("German", "de"), ("Portuguese", "pt"), ("Japanese", "ja"), ("Chinese", "zh")]


class SettingsDialog(QDialog):
    def __init__(self, cfg: Config, status: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Jarvis Settings")
        self.setMinimumWidth(460)
        self.cfg = cfg
        form = QFormLayout()

        self.hotkey = QLineEdit(cfg.hotkey)
        self.hotkey.setPlaceholderText("e.g. ctrl+win, ctrl+alt, ctrl+shift+space, f9")
        form.addRow("Hotkey", self.hotkey)

        self.mode = QComboBox()
        self.mode.addItem("Hold to talk", "hold")
        self.mode.addItem("Press to start / press to stop", "toggle")
        self.mode.setCurrentIndex(max(0, self.mode.findData(cfg.mode)))
        form.addRow("Mode", self.mode)

        self.model = QComboBox()
        self.model.addItems(MODELS)
        self.model.setCurrentText(cfg.model)
        form.addRow("Whisper model", self.model)

        self.device = QComboBox()
        self.device.addItems(["auto", "cuda", "cpu"])
        self.device.setCurrentText(cfg.device)
        form.addRow("Compute device", self.device)

        self.language = QComboBox()
        for label, code in LANGUAGES:
            self.language.addItem(label, code)
        idx = self.language.findData(cfg.language)
        if idx < 0:
            self.language.addItem(cfg.language, cfg.language)
            idx = self.language.count() - 1
        self.language.setCurrentIndex(idx)
        form.addRow("Language", self.language)

        self.mic = QComboBox()
        self.mic.addItem("System default", "")
        for name in list_input_devices():
            self.mic.addItem(name, name)
        self.mic.setCurrentIndex(max(0, self.mic.findData(cfg.input_device)))
        form.addRow("Microphone", self.mic)

        self.words = QPlainTextEdit("\n".join(cfg.custom_words))
        self.words.setPlaceholderText("Names, jargon, product names... one per line")
        self.words.setFixedHeight(70)
        form.addRow("Custom vocabulary", self.words)

        self.fillers = QCheckBox("Remove filler words (um, uh)")
        self.fillers.setChecked(cfg.remove_fillers)
        form.addRow("", self.fillers)

        self.cleanup = QCheckBox("Polish text with a local LLM (requires Ollama)")
        self.cleanup.setChecked(cfg.cleanup_enabled)
        form.addRow("AI cleanup", self.cleanup)
        self.ollama_url = QLineEdit(cfg.ollama_url)
        form.addRow("Ollama URL", self.ollama_url)
        self.ollama_model = QLineEdit(cfg.ollama_model)
        form.addRow("Ollama model", self.ollama_model)

        self.sounds = QCheckBox("Play start/stop sounds")
        self.sounds.setChecked(cfg.sounds)
        form.addRow("", self.sounds)
        self.restore = QCheckBox("Restore clipboard after pasting")
        self.restore.setChecked(cfg.restore_clipboard)
        form.addRow("", self.restore)
        self.autostart = QCheckBox("Start Jarvis when I log in")
        self.autostart.setEnabled(autostart.supported())
        self.autostart.setChecked(autostart.is_enabled())
        form.addRow("", self.autostart)

        self.error = QLabel()
        self.error.setStyleSheet("color: #e5484d")
        info = QLabel(status)
        info.setStyleSheet("color: gray")

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(info)
        layout.addWidget(self.error)
        layout.addWidget(buttons)

    def _save(self) -> None:
        try:
            parse_hotkey(self.hotkey.text())
        except ValueError as e:
            self.error.setText(str(e))
            return
        c = self.cfg
        c.hotkey = self.hotkey.text().strip().lower()
        c.mode = self.mode.currentData()
        c.model = self.model.currentText()
        c.device = self.device.currentText()
        c.language = self.language.currentData()
        c.input_device = self.mic.currentData()
        c.custom_words = [w.strip() for w in self.words.toPlainText().splitlines() if w.strip()]
        c.remove_fillers = self.fillers.isChecked()
        c.cleanup_enabled = self.cleanup.isChecked()
        c.ollama_url = self.ollama_url.text().strip()
        c.ollama_model = self.ollama_model.text().strip()
        c.sounds = self.sounds.isChecked()
        c.restore_clipboard = self.restore.isChecked()
        if autostart.supported():
            autostart.set_enabled(self.autostart.isChecked())
        c.save()
        self.accept()


class HistoryDialog(QDialog):
    def __init__(self, history: History, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Jarvis History")
        self.resize(560, 420)
        self.history = history
        self.list = QListWidget()
        self.list.setWordWrap(True)
        self.list.itemDoubleClicked.connect(self._copy)
        copy_btn = QPushButton("Copy")
        copy_btn.clicked.connect(lambda: self._copy(self.list.currentItem()))
        clear_btn = QPushButton("Clear history")
        clear_btn.clicked.connect(self._clear)
        row = QHBoxLayout()
        row.addWidget(QLabel("Double-click an entry to copy it."))
        row.addStretch()
        row.addWidget(copy_btn)
        row.addWidget(clear_btn)
        layout = QVBoxLayout(self)
        layout.addWidget(self.list)
        layout.addLayout(row)
        self._populate()

    def _populate(self) -> None:
        self.list.clear()
        for item in self.history.load():
            w = QListWidgetItem(f"{item['time']}\n{item['text']}")
            w.setData(Qt.UserRole, item["text"])
            self.list.addItem(w)

    def _copy(self, item) -> None:
        if item:
            QGuiApplication.clipboard().setText(item.data(Qt.UserRole))

    def _clear(self) -> None:
        self.history.clear()
        self._populate()
