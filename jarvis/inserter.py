"""Insert text into the focused app by pasting via the clipboard (handles any Unicode reliably)."""
from __future__ import annotations

import sys
import time


def insert_text(text: str, restore_clipboard: bool = True) -> None:
    import pyperclip
    from pynput.keyboard import Controller, Key

    previous = None
    if restore_clipboard:
        try:
            previous = pyperclip.paste()
        except Exception:
            previous = None

    pyperclip.copy(text)
    time.sleep(0.05)
    kb = Controller()
    with kb.pressed(Key.cmd if sys.platform == "darwin" else Key.ctrl):
        kb.press("v")
        kb.release("v")
    # Give the target app time to read the clipboard before restoring it.
    time.sleep(0.4)
    if previous:
        try:
            pyperclip.copy(previous)
        except Exception:
            pass
