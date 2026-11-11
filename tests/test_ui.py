import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")


def test_overlay_and_dialogs_construct(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_HOME", str(tmp_path))
    from PySide6.QtWidgets import QApplication

    from jarvis.config import Config
    from jarvis.history import History
    from jarvis.ui.dialogs import HistoryDialog, SettingsDialog
    from jarvis.ui.overlay import Overlay

    app = QApplication.instance() or QApplication([])
    o = Overlay()
    o.listening()
    o.push_level(0.1)
    o.grab()
    o.processing()
    o.grab()
    o.flash("Didn't catch that")
    o.grab()
    o.idle()

    cfg = Config()
    dlg = SettingsDialog(cfg, "status")
    dlg.hotkey.setText("ctrl+alt")
    dlg.mode.setCurrentIndex(1)
    dlg._save()
    assert Config.load().hotkey == "ctrl+alt" and Config.load().mode == "toggle"

    h = History(limit=5)
    h.add("hello")
    assert HistoryDialog(h).list.count() == 1
    app.processEvents()
