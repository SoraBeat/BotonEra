"""Main application window – frameless, drag-to-move, sound grid."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QKeyEvent, QKeySequence
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QScrollArea,
    QSizeGrip, QVBoxLayout, QWidget,
)

from src.audio_engine import AudioEngine
from src.sound_manager import SoundEntry, SoundManager
from src.widgets.add_sound_dialog import AddSoundDialog
from src.widgets.flow_layout import FlowLayout
from src.widgets.footer_bar import FooterBar
from src.widgets.header_bar import HeaderBar
from src.widgets.media_player_bar import MediaPlayerBar
from src.widgets.sound_button import AddSoundButton, SoundButton

PAGE_SIZE = 50


class SoundGrid(QWidget):
    """Scrollable area containing all SoundButton widgets + the AddSoundButton."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._layout = FlowLayout(self, h_gap=12, v_gap=12)
        self._layout.setContentsMargins(16, 16, 16, 16)
        self.setLayout(self._layout)

    def add_widget(self, widget: QWidget) -> None:
        self._layout.addWidget(widget)
        self.adjustSize()
        self.updateGeometry()

    def remove_widget(self, widget: QWidget) -> None:
        self._layout.removeWidget(widget)
        widget.setParent(None)
        widget.deleteLater()
        self.adjustSize()
        self.updateGeometry()


# ── Main Window ─────────────────────────────────────────────────────────────

class MainWindow(QWidget):
    def __init__(self, base_dir: Path) -> None:
        super().__init__()

        self._manager = SoundManager(base_dir)
        self._engine = AudioEngine()
        self._engine.set_volume(self._manager.volume)
        self._active_handles: dict[str, object] = {}   # entry.id → PlaybackHandle
        self._sound_buttons: dict[str, SoundButton] = {}  # entry.id → button

        # Lazy loading state
        self._all_entries: list[SoundEntry] = []
        self._filtered_entries: list[SoundEntry] = []
        self._loaded_count: int = 0
        self._loading: bool = False   # re-entrancy guard

        self._setup_window()
        self._build_ui()
        self._populate_sounds()

    # ── Window setup ────────────────────────────────────────────────────────

    def _setup_window(self) -> None:
        self.setWindowTitle("BotonEra")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(620, 480)
        self.resize(820, 580)

    # ── Build UI ────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Card container (gives the window its rounded shape)
        self._card = QFrame(self)
        self._card.setObjectName("main_card")
        self._card.setStyleSheet(
            "#main_card { background:#0A0A0F; border:1px solid #2A2A3E; border-radius:12px; }"
        )
        outer.addWidget(self._card)

        card_layout = QVBoxLayout(self._card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # Header
        self._header = HeaderBar(self._card)
        self._header.set_mic_device(self._manager.mic_device_id)
        self._header.set_monitor_device(self._manager.monitor_device_id)
        self._header.mic_device_changed.connect(self._on_mic_changed)
        self._header.monitor_device_changed.connect(self._on_monitor_changed)
        self._header.add_sound_requested.connect(self._open_add_dialog)
        card_layout.addWidget(self._header)

        # Divider
        div = QFrame(self._card)
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("color:#1E1E2E;")
        card_layout.addWidget(div)

        # Search bar
        self._search_bar = self._build_search_bar(self._card)
        card_layout.addWidget(self._search_bar)

        # Media player bar (hidden until a sound plays)
        self._media_bar = MediaPlayerBar(self._card)
        self._media_bar.setVisible(False)
        self._media_bar.stop_requested.connect(self._on_media_bar_stop)
        card_layout.addWidget(self._media_bar)

        # Scroll area for sound grid (always visible)
        self._scroll = QScrollArea(self._card)
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet("QScrollArea { background:transparent; border:none; }")

        self._grid_widget = SoundGrid()
        self._scroll.setWidget(self._grid_widget)
        card_layout.addWidget(self._scroll, stretch=1)

        # Connect scroll signal for lazy loading
        self._scroll.verticalScrollBar().valueChanged.connect(self._on_scroll_changed)

        # Add sound button (always at end of grid)
        self._add_btn = AddSoundButton()
        self._add_btn.clicked.connect(self._open_add_dialog)
        self._grid_widget.add_widget(self._add_btn)

        # Load-more hint label (below scroll area, above footer)
        self._load_more_label = QLabel("", self._card)
        self._load_more_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._load_more_label.setStyleSheet("color:#3A3A5A; font-size:11px; padding:4px 0;")
        self._load_more_label.setVisible(False)
        card_layout.addWidget(self._load_more_label)

        # Footer
        div2 = QFrame(self._card)
        div2.setFrameShape(QFrame.Shape.HLine)
        div2.setStyleSheet("color:#1E1E2E;")
        card_layout.addWidget(div2)

        self._footer = FooterBar(self._card)
        self._footer.set_volume(self._manager.volume)
        self._footer.stop_all_requested.connect(self._stop_all)
        self._footer.volume_changed.connect(self._on_volume_changed)
        card_layout.addWidget(self._footer)

        # Resize grip
        grip_row = QHBoxLayout()
        grip_row.setContentsMargins(0, 0, 4, 4)
        grip_row.addStretch()
        grip = QSizeGrip(self._card)
        grip.setFixedSize(16, 16)
        grip.setStyleSheet("background:transparent;")
        grip_row.addWidget(grip)
        card_layout.addLayout(grip_row)

    # ── Sound population ────────────────────────────────────────────────────

    def _populate_sounds(self) -> None:
        self._all_entries = list(self._manager.sounds)
        self._filtered_entries = self._all_entries
        self._loaded_count = 0
        self._load_more()
        self._update_empty_state()

    def _load_more(self) -> None:
        if self._loading or self._loaded_count >= len(self._filtered_entries):
            self._update_load_more_label()
            return
        self._loading = True
        try:
            batch = self._filtered_entries[self._loaded_count : self._loaded_count + PAGE_SIZE]
            layout = self._grid_widget._layout

            # Remove AddSoundButton from end temporarily
            last_item = layout.takeAt(layout.count() - 1)

            for entry in batch:
                if entry.id not in self._sound_buttons:
                    btn = SoundButton(entry, self._grid_widget)
                    btn.clicked.connect(self._on_sound_clicked)
                    btn.delete_requested.connect(self._delete_sound)
                    btn.edit_requested.connect(self._edit_sound)
                    self._sound_buttons[entry.id] = btn
                else:
                    btn = self._sound_buttons[entry.id]
                    btn.setParent(self._grid_widget)
                layout.addWidget(btn)
                btn.setVisible(True)

            if last_item and last_item.widget():
                layout.addWidget(last_item.widget())

            self._loaded_count += len(batch)
            self._grid_widget._layout.invalidate()
            self._grid_widget.adjustSize()
            self._grid_widget.updateGeometry()
            self._update_load_more_label()

            # If everything fits without a scrollbar, keep loading until it doesn't
            bar = self._scroll.verticalScrollBar()
            if bar.maximum() == 0 and self._loaded_count < len(self._filtered_entries):
                self._loading = False
                self._load_more()
        finally:
            self._loading = False

    def _on_scroll_changed(self, value: int) -> None:
        bar = self._scroll.verticalScrollBar()
        if bar.maximum() > 0 and value >= bar.maximum() * 0.85:
            self._load_more()

    def _update_load_more_label(self) -> None:
        remaining = len(self._filtered_entries) - self._loaded_count
        if remaining > 0:
            self._load_more_label.setText(f"Desplazate para cargar {remaining} sonidos más…")
            self._load_more_label.setVisible(True)
        else:
            self._load_more_label.setVisible(False)

    def _add_sound_button(self, entry: SoundEntry) -> SoundButton:
        self._all_entries.append(entry)
        if not self._search_edit.text().strip():
            self._filtered_entries = self._all_entries

        btn = SoundButton(entry, self._grid_widget)
        btn.clicked.connect(self._on_sound_clicked)
        btn.delete_requested.connect(self._delete_sound)
        btn.edit_requested.connect(self._edit_sound)
        self._sound_buttons[entry.id] = btn

        layout = self._grid_widget._layout
        last = layout.takeAt(layout.count() - 1)
        layout.addWidget(btn)
        if last and last.widget():
            layout.addWidget(last.widget())
        self._loaded_count += 1

        self._grid_widget.adjustSize()
        self._update_empty_state()
        self._update_load_more_label()
        return btn

    def _update_empty_state(self) -> None:
        pass  # scroll is always visible; + button is always accessible

    # ── Search bar ──────────────────────────────────────────────────────────

    def _build_search_bar(self, parent: QWidget) -> QWidget:
        container = QWidget(parent)
        container.setFixedHeight(46)
        container.setStyleSheet("background: #0C0C14;")

        row = QHBoxLayout(container)
        row.setContentsMargins(14, 6, 14, 6)
        row.setSpacing(8)

        icon = QLabel("🔍", container)
        icon.setFont(QFont("Segoe UI Emoji", 13))
        icon.setStyleSheet("color: #3A3A5A; background: transparent;")
        row.addWidget(icon)

        self._search_edit = QLineEdit(container)
        self._search_edit.setPlaceholderText("Buscar sonidos...")
        self._search_edit.setClearButtonEnabled(True)
        self._search_edit.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #E8E8F0;
                font-size: 13px;
                font-family: 'Segoe UI';
            }
            QLineEdit::placeholder { color: #3A3A5A; }
        """)
        self._search_edit.textChanged.connect(self._filter_sounds)
        row.addWidget(self._search_edit, stretch=1)

        # Bottom separator line
        sep = QFrame(container)
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #1A1A2E;")

        wrap = QVBoxLayout()
        wrap.setContentsMargins(0, 0, 0, 0)
        wrap.setSpacing(0)
        wrap.addWidget(container)
        wrap.addWidget(sep)

        outer = QWidget(parent)
        outer.setLayout(wrap)
        return outer

    def _filter_sounds(self, query: str) -> None:
        q = query.strip().lower()
        self._filtered_entries = (
            [e for e in self._all_entries if q in e.name.lower()] if q
            else self._all_entries
        )

        layout = self._grid_widget._layout
        # Take AddSoundButton off first
        last_item = layout.takeAt(layout.count() - 1)
        # Detach all sound buttons (keep widget objects alive in _sound_buttons)
        while layout.count() > 0:
            item = layout.takeAt(0)
            if item and item.widget():
                item.widget().setVisible(False)
                item.widget().setParent(None)
        if last_item and last_item.widget():
            layout.addWidget(last_item.widget())

        self._loaded_count = 0
        self._grid_widget._layout.invalidate()
        self._grid_widget.adjustSize()
        self._grid_widget.updateGeometry()
        self._load_more()
        self._update_empty_state()
        self._add_btn.setVisible(True)

    # ── Sound playback ──────────────────────────────────────────────────────

    def _on_sound_clicked(self, entry: SoundEntry) -> None:
        # If already playing, stop it
        if entry.id in self._active_handles:
            handle = self._active_handles.pop(entry.id)
            handle.stop()
            if btn := self._sound_buttons.get(entry.id):
                btn.set_playing(False)
            self._media_bar.clear(entry.id)
            return

        # Load audio on demand
        try:
            self._manager.ensure_audio_loaded(entry)
        except Exception as e:
            self._show_error(f"No se pudo cargar el audio:\n{e}")
            return

        btn = self._sound_buttons.get(entry.id)

        def on_done():
            self._active_handles.pop(entry.id, None)
            if btn:
                QTimer.singleShot(0, lambda: btn.set_playing(False))
            QTimer.singleShot(0, lambda: self._media_bar.clear(entry.id))

        handle = self._engine.play(
            entry.audio_data,
            entry.samplerate,
            monitor_device=self._manager.monitor_device_id,
            mic_device=self._manager.mic_device_id,
            on_finished=on_done,
        )
        self._active_handles[entry.id] = handle
        if btn:
            btn.set_playing(True)
        self._media_bar.set_playing(entry, handle)

    def _stop_all(self) -> None:
        self._engine.stop_all()
        self._active_handles.clear()
        for btn in self._sound_buttons.values():
            btn.set_playing(False)
        self._media_bar.clear()

    # ── Add / Edit / Delete ─────────────────────────────────────────────────

    def _open_add_dialog(self) -> None:
        dlg = AddSoundDialog(self)
        if dlg.exec():
            path = Path(dlg.sound_path)
            try:
                entry = self._manager.import_sound(
                    path,
                    dlg.sound_name,
                    dlg.sound_color,
                    dlg.sound_emoji,
                )
                entry.keybind = dlg.sound_keybind
                self._manager.save_config()
                self._add_sound_button(entry)
            except Exception as e:
                self._show_error(f"Error al importar el sonido:\n{e}")

    def _edit_sound(self, sound_id: str) -> None:
        entry = next((s for s in self._manager.sounds if s.id == sound_id), None)
        if not entry:
            return
        dlg = AddSoundDialog(
            self,
            initial_color=entry.color,
            initial_emoji=entry.emoji,
            edit_mode=True,
            entry_name=entry.name,
            entry_keybind=entry.keybind,
        )
        if dlg.exec():
            self._manager.update_sound(
                sound_id,
                name=dlg.sound_name,
                color=dlg.sound_color,
                emoji=dlg.sound_emoji,
                keybind=dlg.sound_keybind,
            )
            if btn := self._sound_buttons.get(sound_id):
                btn.entry.name = dlg.sound_name
                btn.entry.color = dlg.sound_color
                btn.entry.emoji = dlg.sound_emoji
                btn.entry.keybind = dlg.sound_keybind
                btn.update()

    def _delete_sound(self, sound_id: str) -> None:
        self._all_entries = [e for e in self._all_entries if e.id != sound_id]
        self._filtered_entries = [e for e in self._filtered_entries if e.id != sound_id]

        if btn := self._sound_buttons.pop(sound_id, None):
            if h := self._active_handles.pop(sound_id, None):
                h.stop()
            layout = self._grid_widget._layout
            in_layout = any(
                layout.itemAt(i).widget() is btn for i in range(layout.count())
            )
            if in_layout:
                self._grid_widget.remove_widget(btn)
                self._loaded_count -= 1
            else:
                btn.deleteLater()

        self._manager.remove_sound(sound_id)
        self._update_empty_state()
        self._update_load_more_label()

    # ── Media bar ───────────────────────────────────────────────────────────

    def _on_media_bar_stop(self) -> None:
        if self._media_bar._current_entry:
            self._on_sound_clicked(self._media_bar._current_entry)

    # ── Config change handlers ──────────────────────────────────────────────

    def _on_mic_changed(self, device_id) -> None:
        self._manager.mic_device_id = device_id
        self._manager.save_config()

    def _on_monitor_changed(self, device_id) -> None:
        self._manager.monitor_device_id = device_id
        self._manager.save_config()

    def _on_volume_changed(self, value: float) -> None:
        self._manager.volume = value
        self._engine.set_volume(value)
        self._manager.save_config()

    # ── Keyboard shortcuts ──────────────────────────────────────────────────

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if self._search_edit.hasFocus():
            super().keyPressEvent(event)
            return
        key_str = QKeySequence(event.key()).toString()
        for entry in self._manager.sounds:
            if entry.keybind and entry.keybind == key_str:
                self._on_sound_clicked(entry)
                return
        super().keyPressEvent(event)

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _show_error(self, msg: str) -> None:
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Error")
        dlg.setText(msg)
        dlg.setIcon(QMessageBox.Icon.Warning)
        dlg.exec()

    def paintEvent(self, event) -> None:
        pass
