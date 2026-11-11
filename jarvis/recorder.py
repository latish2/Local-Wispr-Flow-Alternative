from __future__ import annotations

import threading
from typing import Callable

import numpy as np

SAMPLE_RATE = 16000


def resample(audio: np.ndarray, src_rate: int, dst_rate: int = SAMPLE_RATE) -> np.ndarray:
    if src_rate == dst_rate or audio.size == 0:
        return audio.astype(np.float32)
    n = int(round(audio.size * dst_rate / src_rate))
    x_old = np.linspace(0.0, 1.0, audio.size, endpoint=False)
    x_new = np.linspace(0.0, 1.0, n, endpoint=False)
    return np.interp(x_new, x_old, audio).astype(np.float32)


def list_input_devices() -> list[str]:
    try:
        import sounddevice as sd

        return [d["name"] for d in sd.query_devices() if d["max_input_channels"] > 0]
    except Exception:
        return []


class Recorder:
    def __init__(self, device: str = "", on_level: Callable[[float], None] | None = None):
        self.device = device or None
        self.on_level = on_level
        self._chunks: list[np.ndarray] = []
        self._stream = None
        self._rate = SAMPLE_RATE
        self._lock = threading.Lock()

    def _callback(self, indata, frames, time_info, status) -> None:
        mono = indata[:, 0].copy()
        with self._lock:
            self._chunks.append(mono)
        if self.on_level:
            self.on_level(float(np.sqrt(np.mean(mono * mono))) if mono.size else 0.0)

    def start(self) -> None:
        import sounddevice as sd

        self._chunks = []
        try:
            self._rate = SAMPLE_RATE
            self._stream = sd.InputStream(
                samplerate=SAMPLE_RATE, channels=1, dtype="float32", device=self.device, callback=self._callback
            )
        except Exception:
            # Some drivers refuse 16 kHz; record at the native rate and resample afterwards.
            info = sd.query_devices(self.device, "input")
            self._rate = int(info["default_samplerate"])
            self._stream = sd.InputStream(
                samplerate=self._rate, channels=1, dtype="float32", device=self.device, callback=self._callback
            )
        self._stream.start()

    def stop(self) -> np.ndarray:
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            finally:
                self._stream = None
        with self._lock:
            audio = np.concatenate(self._chunks) if self._chunks else np.zeros(0, dtype=np.float32)
            self._chunks = []
        return resample(audio, self._rate)
