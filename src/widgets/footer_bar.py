"""Footer bar: Stop All button + master volume slider."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QSlider, QWidget,
)


class FooterBar(QWidget):
    stop_all_requested = pyqtSignal()
    volume_changed = pyqtSignal(float)   # 0.0 – 1.0

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("footer_bar")
        self.setFixedHeight(48)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(10)

        # Stop All
        stop_btn = QPushButton("■  Stop All", self)
        stop_btn.setObjectName("stop_all_btn")
        stop_btn.setToolTip("Detener todos los sonidos en reproducción")
        stop_btn.clicked.connect(self.stop_all_requested)
        layout.addWidget(stop_btn)

        layout.addStretch()

        # Volume icon
        vol_icon = QLabel("🔊", self)
        vol_icon.setFont(QFont("Segoe UI Emoji", 13))
        layout.addWidget(vol_icon)

        # Slider
        self._slider = QSlider(Qt.Orientation.Horizontal, self)
        self._slider.setObjectName("volume_slider")
        self._slider.setRange(0, 100)
        self._slider.setValue(100)
        self._slider.setFixedWidth(140)
        self._slider.setToolTip("Volumen maestro")
        self._slider.valueChanged.connect(self._on_slider)
        layout.addWidget(self._slider)

        # Percentage label
        self._vol_label = QLabel("100%", self)
        self._vol_label.setObjectName("vol_label")
        self._vol_label.setMinimumWidth(36)
        layout.addWidget(self._vol_label)

    def set_volume(self, value: float) -> None:
        v = int(value * 100)
        self._slider.blockSignals(True)
        self._slider.setValue(v)
        self._vol_label.setText(f"{v}%")
        self._slider.blockSignals(False)

    def _on_slider(self, value: int) -> None:
        self._vol_label.setText(f"{value}%")
        self.volume_changed.emit(value / 100.0)
