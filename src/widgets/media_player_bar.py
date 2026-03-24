"""Media player bar – shows currently playing sound with progress and controls."""
from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QLinearGradient, QPainter, QPainterPath
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from src.audio_engine import PlaybackHandle
from src.sound_manager import SoundEntry


class _ProgressBar(QWidget):
    """Purple→cyan gradient fill bar with a white circle handle."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedHeight(6)
        self._progress: float = 0.0

    def set_progress(self, value: float) -> None:
        self._progress = max(0.0, min(1.0, value))
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect()
        radius = 3.0

        # Background track
        bg = QPainterPath()
        bg.addRoundedRect(float(r.x()), float(r.y()), float(r.width()), float(r.height()), radius, radius)
        p.fillPath(bg, QColor("#1A1A26"))

        # Gradient fill
        fill_w = int(r.width() * self._progress)
        if fill_w > 0:
            grad = QLinearGradient(0, 0, r.width(), 0)
            grad.setColorAt(0.0, QColor("#6C63FF"))
            grad.setColorAt(1.0, QColor("#00D9FF"))
            fill = QPainterPath()
            fill.addRoundedRect(float(r.x()), float(r.y()), float(fill_w), float(r.height()), radius, radius)
            p.fillPath(fill, grad)

            # Circle handle at the tip
            p.setBrush(QColor("#FFFFFF"))
            p.setPen(Qt.PenStyle.NoPen)
            cx = r.x() + fill_w
            cy = r.center().y()
            p.drawEllipse(cx - 4, cy - 4, 8, 8)

        p.end()


class MediaPlayerBar(QWidget):
    """Horizontal bar showing current playback info. Hidden when nothing plays."""

    stop_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedHeight(52)
        self.setStyleSheet("background: #0C0C14;")

        self._playing_stack: list[tuple[SoundEntry, PlaybackHandle]] = []
        self._current_entry: SoundEntry | None = None
        self._current_handle: PlaybackHandle | None = None

        self._build_ui()

        self._update_timer = QTimer(self)
        self._update_timer.setInterval(100)
        self._update_timer.timeout.connect(self._tick)

    def _build_ui(self) -> None:
        row = QHBoxLayout(self)
        row.setContentsMargins(14, 0, 14, 0)
        row.setSpacing(10)

        self._emoji_label = QLabel("", self)
        self._emoji_label.setFixedWidth(28)
        self._emoji_label.setFont(QFont("Segoe UI Emoji", 16))
        self._emoji_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(self._emoji_label)

        self._name_label = QLabel("", self)
        self._name_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self._name_label.setStyleSheet("color: #E8E8F0; background: transparent;")
        row.addWidget(self._name_label, stretch=2)

        self._progress_bar = _ProgressBar(self)
        row.addWidget(self._progress_bar, stretch=3)

        self._time_label = QLabel("0:00 / 0:00", self)
        self._time_label.setFixedWidth(80)
        self._time_label.setFont(QFont("Segoe UI", 10))
        self._time_label.setStyleSheet("color: #6B6B8A; background: transparent;")
        self._time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(self._time_label)

        self._stop_btn = QPushButton("⏹", self)
        self._stop_btn.setFixedSize(28, 28)
        self._stop_btn.setFont(QFont("Segoe UI Emoji", 11))
        self._stop_btn.setToolTip("Detener")
        self._stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._stop_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid rgba(108,99,255,0.4);
                border-radius: 6px;
                color: #E8E8F0;
            }
            QPushButton:hover {
                background: rgba(108,99,255,0.25);
                border-color: #6C63FF;
            }
            QPushButton:pressed {
                background: rgba(108,99,255,0.45);
            }
        """)
        self._stop_btn.clicked.connect(self.stop_requested)
        row.addWidget(self._stop_btn)

    # ── Public API ───────────────────────────────────────────────────────────

    def set_playing(self, entry: SoundEntry, handle: PlaybackHandle) -> None:
        # Replace any prior entry for the same sound
        self._playing_stack = [(e, h) for e, h in self._playing_stack if e.id != entry.id]
        self._playing_stack.append((entry, handle))
        self._current_entry = entry
        self._current_handle = handle
        self._refresh_display()
        self.setVisible(True)
        if not self._update_timer.isActive():
            self._update_timer.start()

    def clear(self, sound_id: str | None = None) -> None:
        if sound_id is not None:
            self._playing_stack = [(e, h) for e, h in self._playing_stack if e.id != sound_id]
        else:
            self._playing_stack.clear()

        if self._playing_stack:
            self._current_entry, self._current_handle = self._playing_stack[-1]
            self._refresh_display()
        else:
            self._current_entry = None
            self._current_handle = None
            self._update_timer.stop()
            self.setVisible(False)

    # ── Internal ─────────────────────────────────────────────────────────────

    def _refresh_display(self) -> None:
        if not self._current_entry:
            return
        self._emoji_label.setText(self._current_entry.emoji)
        fm = QFontMetrics(self._name_label.font())
        max_w = self._name_label.width() or 200
        elided = fm.elidedText(self._current_entry.name, Qt.TextElideMode.ElideRight, max_w)
        self._name_label.setText(elided)

    def _tick(self) -> None:
        if not self._current_handle:
            return

        def fmt(s: float) -> str:
            s = int(s)
            return f"{s // 60}:{s % 60:02d}"

        self._progress_bar.set_progress(self._current_handle.progress)
        elapsed = self._current_handle.elapsed_sec
        total = self._current_handle.total_sec
        self._time_label.setText(f"{fmt(elapsed)} / {fmt(total)}")

        # Also refresh name in case label was not sized yet on first call
        if self._current_entry:
            fm = QFontMetrics(self._name_label.font())
            max_w = self._name_label.width() or 200
            elided = fm.elidedText(self._current_entry.name, Qt.TextElideMode.ElideRight, max_w)
            if self._name_label.text() != elided:
                self._name_label.setText(elided)
