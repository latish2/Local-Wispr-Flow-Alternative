from __future__ import annotations

import json
import time
from pathlib import Path

from .config import data_dir


class History:
    def __init__(self, path: Path | None = None, limit: int = 200):
        self.path = Path(path or data_dir() / "history.json")
        self.limit = limit

    def load(self) -> list[dict]:
        try:
            items = json.loads(self.path.read_text(encoding="utf-8"))
            return items if isinstance(items, list) else []
        except (OSError, ValueError):
            return []

    def add(self, text: str, raw: str | None = None) -> None:
        items = self.load()
        items.insert(0, {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "text": text, "raw": raw or text})
        del items[self.limit:]
        self.path.write_text(json.dumps(items, indent=1, ensure_ascii=False), encoding="utf-8")

    def clear(self) -> None:
        self.path.write_text("[]", encoding="utf-8")
