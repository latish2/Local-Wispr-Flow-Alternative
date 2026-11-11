"""Small floating pill near the bottom of the screen showing listening / transcribing state."""
from __future__ import annotations

import math
from collections import deque

from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QApplication, QWidget

BARS = 18


class Overlay(QWidget):
    def __init__(self):
        super().__init__(
            None,
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowDoesNotAcceptFocus,
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.resize(200, 44)
        self.state = "idle"
        self.message = ""
        self.levels: deque[float] = deque([0.0] * BARS, maxlen=BARS)
        self._phase = 0.0
        self._timer = QTimer(self, interval=33, timeout=self._tick)
        self._hide_timer = QTimer(self, singleShot=True, timeout=self.hide)

    def _place(self) -> None:
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.center().x() - self.width() // 2, screen.bottom() - self.height() - 24)

    def push_level(self, rms: float) -> None:
        # Speech RMS is typically 0.01-0.2; map to 0..1 on a soft log-ish curve.
        self.levels.append(min(1.0, math.sqrt(rms * 12)))

    def _show(self, state: str, message: str = "", width: int = 200) -> None:
        self._hide_timer.stop()
        self.state, self.message = state, message
        self.resize(width, 44)
        self._place()
        self.show()
        self.raise_()
        self._timer.start()
        self.update()

    def listening(self) -> None:
        self.levels.extend([0.0] * BARS)
        self._show("listening")

    def processing(self) -> None:
        self._show("processing")

    def flash(self, message: str, ms: int = 2500) -> None:
        width = max(200, QFontMetricsWidth(message) + 48)
        self._show("message", message, width)
        self._hide_timer.start(ms)

    def idle(self) -> None:
        self.state = "idle"
        self._timer.stop()
        self.hide()

    def _tick(self) -> None:
        self._phase += 0.15
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        p.setPen(QPen(QColor(255, 255, 255, 40), 1))
        p.setBrush(QColor(18, 18, 28, 235))
        p.drawRoundedRect(r, r.height() / 2, r.height() / 2)

        grad = QLinearGradient(r.left(), 0, r.right(), 0)
        grad.setColorAt(0, QColor("#7C5CFF"))
        grad.setColorAt(1, QColor("#22D3EE"))

        if self.state == "listening":
            n, gap = BARS, 4
            bw = (r.width() - 40 - gap * (n - 1)) / n
            x = r.left() + 20
            for lvl in self.levels:
                h = 4 + lvl * (r.height() - 16)
                p.setPen(Qt.NoPen)
                p.setBrush(grad)
                p.drawRoundedRect(QRectF(x, r.center().y() - h / 2, bw, h), bw / 2, bw / 2)
                x += bw + gap
        elif self.state == "processing":
            p.setPen(Qt.NoPen)
            for i in range(5):
                a = 0.3 + 0.7 * (0.5 + 0.5 * math.sin(self._phase - i * 0.6))
                c = QColor("#7C5CFF") if i < 2 else QColor("#22D3EE")
                c.setAlphaF(a)
                p.setBrush(c)
                cx = r.center().x() + (i - 2) * 16
                p.drawEllipse(QRectF(cx - 4, r.center().y() - 4, 8, 8))
        elif self.state == "message":
            p.setPen(QColor(235, 235, 245))
            p.setFont(_font())
            p.drawText(r, Qt.AlignCenter, self.message)


def _font() -> QFont:
    f = QFont()
    f.setPointSize(10)
    return f


def QFontMetricsWidth(text: str) -> int:
    from PySide6.QtGui import QFontMetrics

    return QFontMetrics(_font()).horizontalAdvance(text)
