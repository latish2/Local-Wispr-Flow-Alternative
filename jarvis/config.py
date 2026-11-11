from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

APP_NAME = "Jarvis"


def data_dir() -> Path:
    override = os.environ.get("JARVIS_HOME")
    if override:
        base = Path(override)
    elif sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / APP_NAME
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / APP_NAME
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / APP_NAME.lower()
    base.mkdir(parents=True, exist_ok=True)
    return base


@dataclass
class Config:
    hotkey: str = "ctrl+win"
    mode: str = "hold"  # "hold" = push-to-talk, "toggle" = press once to start, again to stop
    model: str = "auto"  # auto picks large-v3-turbo on GPU, base on CPU
    device: str = "auto"  # auto | cuda | cpu
    language: str = ""  # "" = auto-detect, otherwise e.g. "en", "hi"
    custom_words: list[str] = field(default_factory=list)
    remove_fillers: bool = True
    cleanup_enabled: bool = False
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.2:3b"
    input_device: str = ""  # "" = system default
    sounds: bool = True
    restore_clipboard: bool = True
    history_size: int = 200

    @classmethod
    def path(cls) -> Path:
        return data_dir() / "config.json"

    @classmethod
    def load(cls, path: Path | None = None) -> "Config":
        path = path or cls.path()
        cfg = cls()
        try:
            raw = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return cfg
        if not isinstance(raw, dict):
            return cfg
        defaults = asdict(cfg)
        for f in fields(cls):
            if f.name in raw and isinstance(raw[f.name], type(defaults[f.name])):
                setattr(cfg, f.name, raw[f.name])
        return cfg

    def save(self, path: Path | None = None) -> None:
        path = Path(path or self.path())
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        tmp.replace(path)
