"""Dialog to import a new sound: file picker, drag-drop, name, color, emoji, keybind."""
from __future__ import annotations

import os
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QDragEnterEvent, QDropEvent, QFont, QKeyEvent, QKeySequence
from PyQt6.QtWidgets import (
    QDialog, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QVBoxLayout, QWidget,
)

from src.styles.theme import BUTTON_COLORS, BUTTON_EMOJIS

AUDIO_FILTER = "Audio (*.wav *.mp3 *.ogg *.flac *.aiff *.m4a);;Todos los archivos (*)"

QUICK_EMOJIS = [
    "🔊", "💥", "🎵", "🎤", "🥁", "🎸", "🔔", "💣",
    "🎺", "🎻", "🚨", "😂", "💀", "🤣", "🔥", "👏",
    "😎", "🎮", "🚀", "💯", "🎉", "👋", "😱", "🤔",
]


# ── Drag-drop zone ─────────────────────────────────────────────────────────

class DropZone(QLabel):
    file_dropped = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("drop_zone")
        self.setAcceptDrops(True)
        self.setText("Arrastrá un archivo de audio aquí\n\nWAV · MP3 · OGG · FLAC")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(100)
        self.setFont(QFont("Segoe UI", 11))
        self._active = False

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._active = True
            self.setStyleSheet(
                "background:#1E1E32; border:2px dashed #6C63FF; border-radius:12px; color:#6C63FF;"
            )

    def dragLeaveEvent(self, event) -> None:
        self._active = False
        self.setStyleSheet("")

    def dropEvent(self, event: QDropEvent) -> None:
        self._active = False
        self.setStyleSheet("")
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            self.file_dropped.emit(path)


# ── Key capture ────────────────────────────────────────────────────────────

class KeyCaptureEdit(QLineEdit):
    """Read-only field that captures the next key press as a shortcut."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setPlaceholderText("Clic aquí y presioná una tecla")
        self.setReadOnly(True)
        self.setToolTip("Asignar atajo de teclado (opcional)")

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        if key in (Qt.Key.Key_Escape,):
            self.clear()
            return
        if key in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
            self.clear()
            return
        text = QKeySequence(key).toString()
        if text:
            self.setText(text)


# ── Color swatch ───────────────────────────────────────────────────────────

class ColorSwatch(QPushButton):
    def __init__(self, color: str, parent=None) -> None:
        super().__init__(parent)
        self.color = color
        self.setFixedSize(24, 24)
        self.setCheckable(True)
        self._update_style(False)

    def _update_style(self, selected: bool) -> None:
        border = "3px solid #E8E8F0" if selected else "2px solid #2A2A3E"
        self.setStyleSheet(
            f"QPushButton {{ background:{self.color}; border-radius:12px; border:{border}; }}"
            f"QPushButton:hover {{ border:2px solid #E8E8F0; }}"
        )

    def setChecked(self, v: bool) -> None:
        super().setChecked(v)
        self._update_style(v)


# ── Main dialog ────────────────────────────────────────────────────────────

class AddSoundDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None = None,
        initial_color: str | None = None,
        initial_emoji: str | None = None,
        # Edit mode: pre-fill fields (no file picker shown)
        edit_mode: bool = False,
        entry_name: str = "",
        entry_keybind: str = "",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Agregar sonido" if not edit_mode else "Editar sonido")
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumWidth(420)

        self._edit_mode = edit_mode
        self._selected_path: str | None = None
        self._selected_color: str = initial_color or BUTTON_COLORS[0]
        self._selected_emoji: str = initial_emoji or BUTTON_EMOJIS[0]

        self._build_ui(entry_name, entry_keybind)
        self._update_preview_label()

    # ── Properties ─────────────────────────────────────────────────────────

    @property
    def sound_path(self) -> str | None:
        return self._selected_path

    @property
    def sound_name(self) -> str:
        return self._name_edit.text().strip()

    @property
    def sound_color(self) -> str:
        return self._selected_color

    @property
    def sound_emoji(self) -> str:
        return self._selected_emoji

    @property
    def sound_keybind(self) -> str:
        return self._keybind_edit.text().strip()

    # ── Build UI ───────────────────────────────────────────────────────────

    def _build_ui(self, name: str, keybind: str) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # Card container
        card = QFrame(self)
        card.setStyleSheet(
            "QFrame { background:#12121A; border:1px solid #2A2A3E; border-radius:14px; }"
        )
        outer.addWidget(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # ── Title ──────────────────────────────────────────────────────────
        title_row = QHBoxLayout()
        title_lbl = QLabel("🎵  " + ("Agregar sonido" if not self._edit_mode else "Editar sonido"))
        title_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_row.addWidget(title_lbl)
        title_row.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet(
            "QPushButton { background:transparent; border:none; color:#6B6B8A; font-size:14px; border-radius:6px; }"
            "QPushButton:hover { color:#FF6B6B; background:#FF6B6B20; }"
        )
        close_btn.clicked.connect(self.reject)
        title_row.addWidget(close_btn)
        layout.addLayout(title_row)

        # ── Drag-drop zone (only in add mode) ──────────────────────────────
        if not self._edit_mode:
            self._drop_zone = DropZone(card)
            self._drop_zone.file_dropped.connect(self._on_file_dropped)
            layout.addWidget(self._drop_zone)

            browse_btn = QPushButton("📂  Buscar archivo...", card)
            browse_btn.setObjectName("browse_btn")
            browse_btn.clicked.connect(self._browse_file)
            layout.addWidget(browse_btn, alignment=Qt.AlignmentFlag.AlignLeft)

            self._file_label = QLabel("Ningún archivo seleccionado", card)
            self._file_label.setFont(QFont("Segoe UI", 10))
            self._file_label.setStyleSheet("color:#6B6B8A;")
            layout.addWidget(self._file_label)

        # ── Name ───────────────────────────────────────────────────────────
        layout.addWidget(self._section("Nombre del botón"))
        self._name_edit = QLineEdit(name, card)
        self._name_edit.setPlaceholderText("Ej: Drum roll, MLG Horn…")
        layout.addWidget(self._name_edit)

        # ── Color ──────────────────────────────────────────────────────────
        layout.addWidget(self._section("Color"))
        color_row = QHBoxLayout()
        color_row.setSpacing(8)
        self._swatches: list[ColorSwatch] = []
        for c in BUTTON_COLORS:
            sw = ColorSwatch(c, card)
            sw.clicked.connect(lambda _, col=c: self._pick_color(col))
            color_row.addWidget(sw)
            self._swatches.append(sw)
        color_row.addStretch()
        layout.addLayout(color_row)
        self._pick_color(self._selected_color, silent=True)

        # ── Emoji ──────────────────────────────────────────────────────────
        layout.addWidget(self._section("Emoji"))
        emoji_grid = QGridLayout()
        emoji_grid.setSpacing(6)
        self._emoji_btns: list[QPushButton] = []
        for i, em in enumerate(QUICK_EMOJIS):
            btn = QPushButton(em, card)
            btn.setFixedSize(36, 36)
            btn.setFont(QFont("Segoe UI Emoji", 14))
            btn.setStyleSheet(
                "QPushButton { background:#1A1A26; border:1px solid #2A2A3E; border-radius:8px; }"
                "QPushButton:hover { background:#22223A; border-color:#6C63FF; }"
                "QPushButton:checked { background:#6C63FF30; border:1px solid #6C63FF; }"
            )
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, e=em: self._pick_emoji(e))
            emoji_grid.addWidget(btn, i // 8, i % 8)
            self._emoji_btns.append(btn)
        layout.addLayout(emoji_grid)
        self._pick_emoji(self._selected_emoji, silent=True)

        # ── Keybind ────────────────────────────────────────────────────────
        layout.addWidget(self._section("Atajo de teclado (opcional)"))
        self._keybind_edit = KeyCaptureEdit(card)
        self._keybind_edit.setText(keybind)
        layout.addWidget(self._keybind_edit)

        # ── Buttons ────────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancelar", card)
        cancel_btn.setObjectName("cancel_btn")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        self._ok_btn = QPushButton("Agregar" if not self._edit_mode else "Guardar", card)
        self._ok_btn.setObjectName("ok_btn")
        self._ok_btn.clicked.connect(self._on_accept)
        btn_row.addWidget(self._ok_btn)

        layout.addLayout(btn_row)

    # ── Helpers ────────────────────────────────────────────────────────────

    def _section(self, text: str) -> QLabel:
        lbl = QLabel(text.upper())
        lbl.setObjectName("section_label")
        return lbl

    def _update_preview_label(self) -> None:
        if not self._edit_mode and hasattr(self, "_file_label"):
            if self._selected_path:
                self._file_label.setText(f"✓  {Path(self._selected_path).name}")
                self._file_label.setStyleSheet("color:#00FF88; font-size:10px;")
            else:
                self._file_label.setText("Ningún archivo seleccionado")
                self._file_label.setStyleSheet("color:#6B6B8A; font-size:10px;")

    def _browse_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar audio", "", AUDIO_FILTER)
        if path:
            self._on_file_dropped(path)

    def _on_file_dropped(self, path: str) -> None:
        self._selected_path = path
        self._update_preview_label()
        if not self._name_edit.text().strip():
            self._name_edit.setText(Path(path).stem)

    def _pick_color(self, color: str, *, silent: bool = False) -> None:
        self._selected_color = color
        for sw in self._swatches:
            sw.setChecked(sw.color == color)

    def _pick_emoji(self, emoji: str, *, silent: bool = False) -> None:
        self._selected_emoji = emoji
        for btn in self._emoji_btns:
            btn.setChecked(btn.text() == emoji)

    def _on_accept(self) -> None:
        if not self._edit_mode and not self._selected_path:
            self._drop_zone.setStyleSheet(
                "background:#2A1515; border:2px dashed #FF6B6B; border-radius:12px; color:#FF6B6B;"
            )
            QTimer.singleShot(1200, lambda: self._drop_zone.setStyleSheet(""))
            return
        if not self._name_edit.text().strip():
            self._name_edit.setStyleSheet(
                "border:1px solid #FF6B6B; background:#2A1515; border-radius:8px; padding:8px 12px;"
            )
            QTimer.singleShot(1200, lambda: self._name_edit.setStyleSheet(""))
            return
        self.accept()

    # ── Drag title bar ─────────────────────────────────────────────────────

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event) -> None:
        if hasattr(self, "_drag_pos") and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
