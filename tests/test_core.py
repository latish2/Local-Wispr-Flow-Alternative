import json
import types

import numpy as np
import pytest

from jarvis import cleanup
from jarvis.config import Config
from jarvis.history import History
from jarvis.hotkey import HotkeyState, display_hotkey, key_name, parse_hotkey
from jarvis.recorder import resample


def test_parse_and_display_hotkey():
    assert parse_hotkey("Ctrl + Win") == {"ctrl", "cmd"}
    assert parse_hotkey("ctrl_r+alt_gr+space") == {"ctrl", "alt", "space"}
    assert display_hotkey("win+ctrl") == "Ctrl+Win"
    with pytest.raises(ValueError):
        parse_hotkey(" + ")


def test_key_name_variants():
    assert key_name(types.SimpleNamespace(name="ctrl_l")) == "ctrl"
    assert key_name(types.SimpleNamespace(name="cmd_r")) == "cmd"
    assert key_name(types.SimpleNamespace(char="A", vk=65)) == "a"
    # Ctrl+A on Windows yields a control char; fall back to the virtual-key code.
    assert key_name(types.SimpleNamespace(char="\x01", vk=65)) == "a"
    assert key_name(types.SimpleNamespace(char=None, vk=None)) is None


def test_hold_state_machine():
    s = HotkeyState(parse_hotkey("ctrl+win"))
    assert s.press("ctrl") is None
    assert s.press("cmd") == "activate"
    assert s.press("cmd") is None  # key repeat does not re-trigger
    assert s.press("esc") == "cancel"
    assert s.release("esc") is None
    assert s.release("ctrl") == "deactivate"
    assert s.release("cmd") is None
    assert s.press("cmd") is None
    assert s.press("ctrl") == "activate"


def test_config_roundtrip_and_bad_values(tmp_path):
    p = tmp_path / "config.json"
    c = Config(hotkey="f9", custom_words=["Latish"], cleanup_enabled=True)
    c.save(p)
    assert Config.load(p) == c
    p.write_text(json.dumps({"hotkey": 5, "mode": "toggle", "unknown": 1}))
    loaded = Config.load(p)
    assert loaded.hotkey == "ctrl+win" and loaded.mode == "toggle"
    p.write_text("not json")
    assert Config.load(p) == Config()


def test_history_limit(tmp_path):
    h = History(tmp_path / "h.json", limit=3)
    for i in range(5):
        h.add(f"t{i}")
    assert [x["text"] for x in h.load()] == ["t4", "t3", "t2"]
    h.clear()
    assert h.load() == []


def test_remove_fillers():
    assert cleanup.remove_fillers("Um, so I think, uh, we should go.") == "So I think, we should go."
    assert cleanup.remove_fillers("Umbrella and summer") == "Umbrella and summer"


def test_ollama_cleanup_success_and_fallback(monkeypatch):
    class Resp:
        def __init__(self, body):
            self.body = body

        def read(self):
            return json.dumps({"response": self.body}).encode()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(cleanup.urllib.request, "urlopen", lambda req, timeout: Resp(' "Meet at 6." '))
    assert cleanup.ollama_cleanup("meet at 5 no 6", "http://x", "m") == "Meet at 6."

    monkeypatch.setattr(cleanup.urllib.request, "urlopen", lambda req, timeout: Resp("x" * 1000))
    assert cleanup.ollama_cleanup("short", "http://x", "m") == "short"

    def boom(req, timeout):
        raise OSError("connection refused")

    monkeypatch.setattr(cleanup.urllib.request, "urlopen", boom)
    assert cleanup.ollama_cleanup("raw text", "http://x", "m") == "raw text"


def test_resample():
    a = np.sin(np.linspace(0, 100, 48000)).astype(np.float32)
    out = resample(a, 48000)
    assert out.dtype == np.float32 and out.size == 16000
