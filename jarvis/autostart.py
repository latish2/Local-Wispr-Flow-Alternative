"""Launch-at-login via the per-user Run registry key (Windows only)."""
from __future__ import annotations

import sys
from pathlib import Path

_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_NAME = "Jarvis"


def supported() -> bool:
    return sys.platform == "win32"


def _command() -> str:
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    exe = pythonw if pythonw.exists() else Path(sys.executable)
    script = Path(__file__).resolve().parents[1] / "run_jarvis.py"
    return f'"{exe}" "{script}"'


def is_enabled() -> bool:
    if not supported():
        return False
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _KEY) as k:
            winreg.QueryValueEx(k, _NAME)
            return True
    except OSError:
        return False


def set_enabled(enabled: bool) -> None:
    if not supported():
        return
    import winreg

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _KEY, 0, winreg.KEY_SET_VALUE) as k:
        if enabled:
            winreg.SetValueEx(k, _NAME, 0, winreg.REG_SZ, _command())
        else:
            try:
                winreg.DeleteValue(k, _NAME)
            except OSError:
                pass
