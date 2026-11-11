"""Global hold-to-talk hotkey built on pynput."""
from __future__ import annotations

import threading
import time
from typing import Callable

_ALIASES = {
    "control": "ctrl", "ctrl_l": "ctrl", "ctrl_r": "ctrl",
    "win": "cmd", "windows": "cmd", "super": "cmd", "meta": "cmd", "cmd_l": "cmd", "cmd_r": "cmd",
    "alt_l": "alt", "alt_r": "alt", "alt_gr": "alt", "option": "alt",
    "shift_l": "shift", "shift_r": "shift",
    "return": "enter", "escape": "esc", "spacebar": "space",
}

_DISPLAY = {"cmd": "Win", "ctrl": "Ctrl", "alt": "Alt", "shift": "Shift"}


def normalize(name: str) -> str:
    name = name.strip().lower().replace(" ", "_")
    return _ALIASES.get(name, name)


def parse_hotkey(text: str) -> frozenset[str]:
    keys = frozenset(normalize(p) for p in text.split("+") if p.strip())
    if not keys:
        raise ValueError("Hotkey is empty")
    return keys


def display_hotkey(text: str) -> str:
    order = ["ctrl", "cmd", "alt", "shift"]
    keys = sorted(parse_hotkey(text), key=lambda k: (order.index(k) if k in order else 99, k))
    return "+".join(_DISPLAY.get(k, k.upper() if len(k) == 1 else k.capitalize()) for k in keys)


def key_name(key) -> str | None:
    """Map a pynput Key/KeyCode to a normalized name."""
    name = getattr(key, "name", None)
    if name:
        return normalize(name)
    char = getattr(key, "char", None)
    if char and char.isprintable():
        return normalize(char)
    vk = getattr(key, "vk", None)
    # With Ctrl held, Windows reports control chars; fall back to the virtual-key code.
    if vk is not None and (48 <= vk <= 57 or 65 <= vk <= 90):
        return chr(vk).lower()
    return None


class HotkeyState:
    """Pure state machine: feed key names, get activate/deactivate/cancel events."""

    def __init__(self, combo: frozenset[str], cancel_key: str = "esc"):
        self.combo = combo
        self.cancel_key = cancel_key
        self.pressed: set[str] = set()
        self.active = False

    def press(self, name: str | None) -> str | None:
        if name is None:
            return None
        self.pressed.add(name)
        if name == self.cancel_key and self.cancel_key not in self.combo:
            return "cancel"
        if not self.active and self.combo <= self.pressed:
            self.active = True
            return "activate"
        return None

    def release(self, name: str | None) -> str | None:
        if name is None:
            return None
        self.pressed.discard(name)
        if self.active and name in self.combo:
            self.active = False
            return "deactivate"
        return None


class HotkeyListener:
    def __init__(
        self,
        hotkey: str,
        on_activate: Callable[[], None],
        on_deactivate: Callable[[], None],
        on_cancel: Callable[[], None] | None = None,
    ):
        self.state = HotkeyState(parse_hotkey(hotkey))
        self._callbacks = {"activate": on_activate, "deactivate": on_deactivate, "cancel": on_cancel}
        self._listener = None
        self._lock = threading.Lock()

    def _dispatch(self, event: str | None) -> None:
        cb = self._callbacks.get(event) if event else None
        if cb:
            cb()

    def _on_press(self, key) -> None:
        with self._lock:
            event = self.state.press(key_name(key))
        self._dispatch(event)

    def _on_release(self, key) -> None:
        with self._lock:
            event = self.state.release(key_name(key))
        self._dispatch(event)

    def start(self) -> None:
        from pynput import keyboard

        self._listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        self._listener.daemon = True
        self._listener.start()

    def stop(self) -> None:
        if self._listener:
            self._listener.stop()
            self._listener = None

    def wait_released(self, timeout: float = 2.0) -> None:
        """Block until no modifier keys are held, so a synthetic Ctrl+V isn't combined with them."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with self._lock:
                if not (self.state.pressed & {"ctrl", "cmd", "alt", "shift"}):
                    return
            time.sleep(0.02)
