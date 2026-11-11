from __future__ import annotations

import logging
import os
import site
import sys
from pathlib import Path

import numpy as np

from .config import Config, data_dir
from .recorder import SAMPLE_RATE

log = logging.getLogger(__name__)

MODELS = ["auto", "tiny", "base", "small", "medium", "distil-large-v3", "large-v3-turbo", "large-v3"]


def _register_cuda_dlls() -> None:
    """Make pip-installed nvidia-cublas/cudnn DLLs visible to CTranslate2 on Windows."""
    if sys.platform != "win32":
        return
    roots = [Path(p) for p in site.getsitepackages()]
    try:
        roots.append(Path(site.getusersitepackages()))
    except Exception:
        pass
    if getattr(sys, "_MEIPASS", None):
        roots.append(Path(sys._MEIPASS))
    for root in roots:
        for bin_dir in (root / "nvidia").glob("*/bin"):
            try:
                os.add_dll_directory(str(bin_dir))
            except OSError:
                continue
            os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")


def _cuda_available() -> bool:
    try:
        import ctranslate2

        return ctranslate2.get_cuda_device_count() > 0
    except Exception:
        return False


class Transcriber:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.model = None
        self.device = "cpu"
        self.model_name = ""

    def load(self) -> str:
        """Load the model (downloads on first use). Returns a human-readable description."""
        _register_cuda_dlls()
        from faster_whisper import WhisperModel

        want = self.cfg.device
        use_cuda = want == "cuda" or (want == "auto" and _cuda_available())
        attempts = [("cuda", "int8_float16")] if use_cuda else []
        attempts.append(("cpu", "int8"))

        last_err: Exception | None = None
        for device, compute in attempts:
            name = self.cfg.model if self.cfg.model != "auto" else ("large-v3-turbo" if device == "cuda" else "base")
            try:
                model = WhisperModel(name, device=device, compute_type=compute, download_root=str(data_dir() / "models"))
                # Missing cuDNN/cuBLAS usually only surfaces at first inference, so warm up here.
                list(model.transcribe(np.zeros(SAMPLE_RATE, dtype=np.float32), language="en")[0])
            except Exception as e:  # noqa: BLE001
                log.warning("Could not load %s on %s: %s", name, device, e)
                last_err = e
                continue
            self.model, self.device, self.model_name = model, device, name
            return f"{name} on {'GPU' if device == 'cuda' else 'CPU'}"
        raise RuntimeError(f"Failed to load Whisper model: {last_err}")

    def transcribe(self, audio: np.ndarray) -> str:
        if self.model is None:
            raise RuntimeError("Model not loaded")
        if audio.size < SAMPLE_RATE * 0.3 or float(np.max(np.abs(audio))) < 0.005:
            return ""
        prompt = ", ".join(w.strip() for w in self.cfg.custom_words if w.strip()) or None
        segments, _info = self.model.transcribe(
            audio,
            language=self.cfg.language or None,
            beam_size=5,
            vad_filter=True,
            condition_on_previous_text=False,
            initial_prompt=prompt,
        )
        return " ".join(s.text.strip() for s in segments).strip()
