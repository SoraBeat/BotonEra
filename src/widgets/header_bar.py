"""Custom frameless header bar: logo, title, device selectors, window controls."""
from __future__ import annotations

import os

from PyQt6.QtCore import QPoint, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QColor, QFont, QIcon, QPainter, QPainterPath, QPixmap,
)
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QPushButton, QWidget,
)

from src.device_manager import get_output_devices
from src.styles.theme import ACCENT_CYAN, ACCENT_PURPLE, TEXT_SECONDARY


def _load_svg_icon(path: str, size: int = 28) -> QPixmap:
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    renderer = QSvgRenderer(path)
    painter = QPainter(pix)
    renderer.render(painter)
    painter.end()
    return pix


class _LogoWidget(QWidget):
    """Draws the BotonEra SVG logo with a subtle animated shimmer."""

    def __init__(self, svg_path: str, size: int = 32, parent=None) -> None:
        super().__init__(parent)
        self._pix = _load_svg_icon(svg_path, size)
        self.setFixedSize(size, size)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.drawPixmap(0, 0, self._pix)
        p.end()


class _DeviceCombo(QComboBox):
    """Styled device selector with a custom drop-arrow drawn in paintEvent."""

    def __init__(self, placeholder: str, parent=None) -> None:
        super().__init__(parent)
        self._placeholder = placeholder
        self.setPlaceholderText(placeholder)
        self.setCurrentIndex(-1)
        self.setToolTip(placeholder)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        # Draw custom arrow
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        arrow_x = self.width() - 18
        arrow_y = self.height() // 2 - 2
        p.setPen(QColor(TEXT_SECONDARY))
        p.setFont(QFont("Segoe UI", 8))
        p.drawText(arrow_x, arrow_y + 8, "▾")
        p.end()


class HeaderBar(QWidget):
    """Frameless header: drag-to-move, logo, title, device dropdowns, window btns."""

    mic_device_changed = pyqtSignal(object)      # int | None
    monitor_device_changed = pyqtSignal(object)  # int | None
    add_sound_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("header_bar")
        self.setFixedHeight(56)

        self._drag_pos: QPoint | None = None
        self._devices: list[dict] = []

        self._build_ui()
        self.refresh_devices()

    # ── Layout ─────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 8, 0)
        layout.setSpacing(0)

        # Logo — in frozen .exe, bundled assets live in sys._MEIPASS
        import sys as _sys
        if getattr(_sys, "frozen", False):
            assets_dir = os.path.join(_sys._MEIPASS, "assets")
        else:
            assets_dir = os.path.join(os.path.dirname(__file__), "..", "..", "assets")
        svg_path = os.path.normpath(os.path.join(assets_dir, "logo.svg"))
        if os.path.exists(svg_path):
            self._logo = _LogoWidget(svg_path, 28, self)
            layout.addWidget(self._logo)
            layout.addSpacing(10)

        # Title
        title = QLabel("BotonEra")
        title.setObjectName("app_title")
        layout.addWidget(title)

        layout.addStretch()

        # Mic device selector
        mic_lbl = QLabel("🎤")
        mic_lbl.setToolTip("Salida a Discord (cable virtual)")
        mic_lbl.setFont(QFont("Segoe UI Emoji", 13))
        layout.addWidget(mic_lbl)
        layout.addSpacing(4)

        self._mic_combo = _DeviceCombo("Discord Mic — sin configurar", self)
        self._mic_combo.setToolTip(
            "Seleccioná el dispositivo que Discord usa como micrófono.\n"
            "Necesitás tener instalado VB-Audio Virtual Cable."
        )
        self._mic_combo.currentIndexChanged.connect(self._on_mic_changed)
        layout.addWidget(self._mic_combo)

        layout.addSpacing(12)

        # Monitor device selector
        mon_lbl = QLabel("🎧")
        mon_lbl.setToolTip("Salida para auriculares")
        mon_lbl.setFont(QFont("Segoe UI Emoji", 13))
        layout.addWidget(mon_lbl)
        layout.addSpacing(4)

        self._monitor_combo = _DeviceCombo("Auriculares — por defecto", self)
        self._monitor_combo.setToolTip("Dispositivo donde escuchás vos los sonidos.")
        self._monitor_combo.currentIndexChanged.connect(self._on_monitor_changed)
        layout.addWidget(self._monitor_combo)

        layout.addSpacing(16)

        # Add sound button
        self._header_add_btn = QPushButton("+", self)
        self._header_add_btn.setObjectName("btn_add_sound")
        self._header_add_btn.setFixedSize(28, 28)
        self._header_add_btn.setToolTip("Agregar sonido")
        self._header_add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header_add_btn.clicked.connect(self.add_sound_requested)
        layout.addWidget(self._header_add_btn)
        layout.addSpacing(8)

        # Window control buttons
        for obj_name, label, tip in [
            ("btn_minimize", "─", "Minimizar"),
            ("btn_maximize", "□", "Maximizar"),
            ("btn_close",   "✕", "Cerrar"),
        ]:
            btn = QPushButton(label, self)
            btn.setObjectName(obj_name)
            btn.setToolTip(tip)
            btn.setFixedSize(30, 30)
            layout.addWidget(btn)
            layout.addSpacing(2)

        # Wire close/minimize
        self._find_btn("btn_close").clicked.connect(
            lambda: self.window().close()
        )
        self._find_btn("btn_minimize").clicked.connect(
            lambda: self.window().showMinimized()
        )
        self._find_btn("btn_maximize").clicked.connect(self._toggle_maximize)

    # ── Device refresh ─────────────────────────────────────────────────────

    def refresh_devices(self) -> None:
        self._devices = get_output_devices()

        for combo in (self._mic_combo, self._monitor_combo):
            combo.blockSignals(True)
            current_id = combo.currentData()
            combo.clear()
            combo.addItem("— Sin asignar —", userData=None)
            for d in self._devices:
                combo.addItem(d["name"], userData=d["id"])
            # Restore selection
            if current_id is not None:
                idx = combo.findData(current_id)
                combo.setCurrentIndex(idx if idx >= 0 else 0)
            else:
                combo.setCurrentIndex(0)
            combo.blockSignals(False)

    def set_mic_device(self, device_id: int | None) -> None:
        idx = self._mic_combo.findData(device_id)
        self._mic_combo.blockSignals(True)
        self._mic_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self._mic_combo.blockSignals(False)

    def set_monitor_device(self, device_id: int | None) -> None:
        idx = self._monitor_combo.findData(device_id)
        self._monitor_combo.blockSignals(True)
        self._monitor_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self._monitor_combo.blockSignals(False)

    # ── Drag-to-move ───────────────────────────────────────────────────────

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.window().pos()

    def mouseMoveEvent(self, event) -> None:
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.window().move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event) -> None:
        self._drag_pos = None

    def mouseDoubleClickEvent(self, event) -> None:
        self._toggle_maximize()

    # ── Internal ───────────────────────────────────────────────────────────

    def _on_mic_changed(self, index: int) -> None:
        self.mic_device_changed.emit(self._mic_combo.currentData())

    def _on_monitor_changed(self, index: int) -> None:
        self.monitor_device_changed.emit(self._monitor_combo.currentData())

    def _toggle_maximize(self) -> None:
        win = self.window()
        if win.isMaximized():
            win.showNormal()
        else:
            win.showMaximized()

    def _find_btn(self, name: str) -> QPushButton:
        return self.findChild(QPushButton, name)
