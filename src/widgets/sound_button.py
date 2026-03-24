"""Custom sound-board button with glow, pulse, and context-menu animations."""
from __future__ import annotations

from PyQt6.QtCore import (
    QEasingCurve, QPoint, QPropertyAnimation, QRect, QSize, Qt, QTimer,
    pyqtProperty, pyqtSignal,
)
from PyQt6.QtGui import (
    QColor, QFont, QFontMetrics, QPainter, QPainterPath,
    QPen, QRadialGradient,
)
from PyQt6.QtWidgets import (
    QGraphicsDropShadowEffect, QMenu, QSizePolicy, QWidget,
)

from src.sound_manager import SoundEntry


class SoundButton(QWidget):
    """A card-style button representing a single sound."""

    clicked = pyqtSignal(object)        # emits SoundEntry
    delete_requested = pyqtSignal(str)  # emits entry.id
    edit_requested = pyqtSignal(str)    # emits entry.id

    _BTN_W = 140
    _BTN_H = 118

    def __init__(self, entry: SoundEntry, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.entry = entry
        self._hovered = False
        self._pressed = False
        self._playing = False
        self._pulse = 0.0          # 0.0 → 1.0 → 0.0
        self._pulse_dir = 1

        self.setFixedSize(self._BTN_W, self._BTN_H)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)

        # Drop-shadow glow
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(0)
        self._shadow.setOffset(0, 0)
        self._shadow.setColor(QColor(entry.color))
        self.setGraphicsEffect(self._shadow)

        # Hover: animate glow radius 0 → 18
        self._hover_anim = QPropertyAnimation(self._shadow, b"blurRadius", self)
        self._hover_anim.setDuration(180)
        self._hover_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Playing pulse timer (30 fps)
        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(33)
        self._pulse_timer.timeout.connect(self._tick_pulse)

        # Click ripple
        self._ripple_radius = 0
        self._ripple_alpha = 0
        self._ripple_anim = QPropertyAnimation(self, b"rippleRadius", self)
        self._ripple_anim.setDuration(350)
        self._ripple_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._ripple_anim.setStartValue(0)
        self._ripple_anim.setEndValue(100)

    # ── Qt property for ripple animation ───────────────────────────────────

    def _get_ripple_radius(self) -> int:
        return self._ripple_radius

    def _set_ripple_radius(self, value: int) -> None:
        self._ripple_radius = value
        self._ripple_alpha = max(0, 180 - value * 2)
        self.update()

    rippleRadius = pyqtProperty(int, fget=_get_ripple_radius, fset=_set_ripple_radius)

    # ── Public ─────────────────────────────────────────────────────────────

    def set_playing(self, playing: bool) -> None:
        self._playing = playing
        if playing:
            self._pulse = 0.0
            self._pulse_dir = 1
            self._pulse_timer.start()
        else:
            self._pulse_timer.stop()
            self._pulse = 0.0
            self._shadow.setColor(QColor(self.entry.color))
            self.update()

    # ── Mouse events ───────────────────────────────────────────────────────

    def enterEvent(self, event) -> None:
        self._hovered = True
        self._hover_anim.stop()
        self._hover_anim.setStartValue(int(self._shadow.blurRadius()))
        self._hover_anim.setEndValue(18)
        self._hover_anim.start()
        self.update()

    def leaveEvent(self, event) -> None:
        self._hovered = False
        if not self._playing:
            self._hover_anim.stop()
            self._hover_anim.setStartValue(int(self._shadow.blurRadius()))
            self._hover_anim.setEndValue(0)
            self._hover_anim.start()
        self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
            self._ripple_anim.stop()
            self._ripple_radius = 0
            self._ripple_alpha = 180
            self._ripple_anim.start()
            self.update()
        elif event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._pressed:
            self._pressed = False
            self.update()
            if self.rect().contains(event.position().toPoint()):
                self.clicked.emit(self.entry)

    # ── Painting ───────────────────────────────────────────────────────────

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        r = self.rect().adjusted(2, 2, -2, -2)
        radius = 14.0

        # ── Card background ────────────────────────────────────────────────
        path = QPainterPath()
        path.addRoundedRect(float(r.x()), float(r.y()),
                            float(r.width()), float(r.height()), radius, radius)

        if self._pressed:
            fill = QColor("#14142A")
        elif self._hovered:
            fill = QColor("#22223A")
        else:
            fill = QColor("#1A1A26")
        p.fillPath(path, fill)

        # ── Border ─────────────────────────────────────────────────────────
        accent = QColor(self.entry.color)
        if self._playing:
            alpha = int(80 + self._pulse * 160)
            accent.setAlpha(alpha)
            pen = QPen(accent, 2.0)
        elif self._hovered:
            accent.setAlpha(180)
            pen = QPen(accent, 1.5)
        else:
            accent.setAlpha(55)
            pen = QPen(accent, 1.0)
        p.setPen(pen)
        p.drawPath(path)

        # ── Top accent bar ─────────────────────────────────────────────────
        bar_h = 3
        bar_path = QPainterPath()
        bar_path.addRoundedRect(
            float(r.x()), float(r.y()),
            float(r.width()), float(bar_h),
            radius / 2, radius / 2,
        )
        bar_color = QColor(self.entry.color)
        if self._playing:
            bar_color.setAlphaF(0.5 + self._pulse * 0.5)
        else:
            bar_color.setAlphaF(0.7 if self._hovered else 0.45)
        p.fillPath(bar_path, bar_color)

        # ── Ripple overlay ─────────────────────────────────────────────────
        if self._ripple_radius > 0 and self._ripple_alpha > 0:
            p.save()
            p.setClipPath(path)
            rip_color = QColor(self.entry.color)
            rip_color.setAlpha(self._ripple_alpha)
            rip_w = int(r.width() * self._ripple_radius / 100)
            cx = r.center().x()
            cy = r.center().y()
            grad = QRadialGradient(cx, cy, rip_w)
            grad.setColorAt(0.0, rip_color)
            rip_color2 = QColor(rip_color)
            rip_color2.setAlpha(0)
            grad.setColorAt(1.0, rip_color2)
            p.setBrush(grad)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPoint(cx, cy), rip_w, rip_w)
            p.restore()

        # ── Emoji ──────────────────────────────────────────────────────────
        emoji_font = QFont("Segoe UI Emoji", 26)
        p.setFont(emoji_font)
        p.setPen(Qt.PenStyle.NoPen)
        emoji_rect = QRect(r.x(), r.y() + bar_h + 8, r.width(), 40)
        p.setPen(QColor("#FFFFFF"))
        p.drawText(emoji_rect, Qt.AlignmentFlag.AlignCenter, self.entry.emoji)

        # ── Name ───────────────────────────────────────────────────────────
        name_font = QFont("Segoe UI", 10, QFont.Weight.Medium)
        p.setFont(name_font)
        name_color = QColor("#E8E8F0") if not self._pressed else QColor("#C0C0D8")
        p.setPen(name_color)
        name_rect = QRect(r.x() + 6, r.y() + bar_h + 52, r.width() - 12, 30)
        p.drawText(name_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop
                   | Qt.TextFlag.TextWordWrap, self.entry.name)

        # ── Keybind pill ───────────────────────────────────────────────────
        if self.entry.keybind:
            kb_font = QFont("Segoe UI", 8, QFont.Weight.Bold)
            p.setFont(kb_font)
            fm = QFontMetrics(kb_font)
            kb_text = self.entry.keybind
            tw = fm.horizontalAdvance(kb_text)
            pill_w = tw + 10
            pill_h = 16
            pill_x = r.right() - pill_w - 6
            pill_y = r.bottom() - pill_h - 5
            pill = QPainterPath()
            pill.addRoundedRect(float(pill_x), float(pill_y),
                                float(pill_w), float(pill_h), 4, 4)
            pill_bg = QColor(self.entry.color)
            pill_bg.setAlpha(40)
            p.fillPath(pill, pill_bg)
            p.setPen(QColor(self.entry.color))
            p.drawText(
                QRect(pill_x, pill_y, pill_w, pill_h),
                Qt.AlignmentFlag.AlignCenter,
                kb_text,
            )

        # ── Playing indicator dot ──────────────────────────────────────────
        if self._playing:
            dot_r = 4
            dot_x = r.x() + 9
            dot_y = r.bottom() - 9
            dot_color = QColor("#00FF88")
            dot_color.setAlphaF(0.6 + self._pulse * 0.4)
            p.setBrush(dot_color)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPoint(dot_x, dot_y), dot_r, dot_r)

        p.end()

    # ── Internal ───────────────────────────────────────────────────────────

    def _tick_pulse(self) -> None:
        self._pulse += self._pulse_dir * 0.06
        if self._pulse >= 1.0:
            self._pulse = 1.0
            self._pulse_dir = -1
        elif self._pulse <= 0.0:
            self._pulse = 0.0
            self._pulse_dir = 1
        # Animate shadow color intensity
        c = QColor(self.entry.color)
        c.setAlphaF(0.4 + self._pulse * 0.6)
        self._shadow.setColor(c)
        self._shadow.setBlurRadius(12 + self._pulse * 14)
        self.update()

    def _show_context_menu(self, pos: QPoint) -> None:
        menu = QMenu(self)
        menu.setWindowFlags(menu.windowFlags() | Qt.WindowType.NoDropShadowWindowHint)
        rename_act = menu.addAction("✏️  Renombrar")
        color_act = menu.addAction("🎨  Cambiar color")
        emoji_act = menu.addAction("😀  Cambiar emoji")
        keybind_act = menu.addAction("⌨️  Asignar tecla")
        menu.addSeparator()
        delete_act = menu.addAction("🗑️  Eliminar")

        chosen = menu.exec(pos)
        if chosen == delete_act:
            self.delete_requested.emit(self.entry.id)
        elif chosen in (rename_act, color_act, emoji_act, keybind_act):
            self.edit_requested.emit(self.entry.id)

    def sizeHint(self) -> QSize:
        return QSize(self._BTN_W, self._BTN_H)


# ── Add-sound placeholder button ───────────────────────────────────────────

class AddSoundButton(QWidget):
    """The '+' card that lives at the end of the grid."""

    clicked = pyqtSignal()

    _BTN_W = SoundButton._BTN_W
    _BTN_H = SoundButton._BTN_H

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._hovered = False
        self._pulse = 0.0
        self._pulse_dir = 1
        self.setFixedSize(self._BTN_W, self._BTN_H)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(50)
        self._pulse_timer.timeout.connect(self._tick)

    def enterEvent(self, event) -> None:
        self._hovered = True
        self._pulse_timer.start()
        self.update()

    def leaveEvent(self, event) -> None:
        self._hovered = False
        self._pulse_timer.stop()
        self._pulse = 0.0
        self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        r = self.rect().adjusted(2, 2, -2, -2)
        radius = 14.0

        path = QPainterPath()
        path.addRoundedRect(float(r.x()), float(r.y()),
                            float(r.width()), float(r.height()), radius, radius)

        p.fillPath(path, QColor("#131320" if self._hovered else "#0F0F1C"))

        # Dashed border
        border_color = QColor("#6C63FF" if self._hovered else "#2A2A3E")
        if self._hovered:
            border_color.setAlphaF(0.5 + self._pulse * 0.5)
        pen = QPen(border_color, 1.8, Qt.PenStyle.DashLine)
        pen.setDashPattern([5, 4])
        p.setPen(pen)
        p.drawPath(path)

        # "+" icon
        plus_font = QFont("Segoe UI", 28, QFont.Weight.Light)
        p.setFont(plus_font)
        plus_color = QColor("#6C63FF" if self._hovered else "#3A3A5A")
        plus_color.setAlphaF(0.7 + self._pulse * 0.3 if self._hovered else 1.0)
        p.setPen(plus_color)
        p.drawText(r.adjusted(0, -8, 0, -8), Qt.AlignmentFlag.AlignCenter, "+")

        # "Agregar sonido" label
        lbl_font = QFont("Segoe UI", 9)
        p.setFont(lbl_font)
        lbl_color = QColor("#6C63FF" if self._hovered else "#3A3A5A")
        p.setPen(lbl_color)
        lbl_rect = QRect(r.x(), r.center().y() + 14, r.width(), 20)
        p.drawText(lbl_rect, Qt.AlignmentFlag.AlignCenter, "Agregar sonido")

        p.end()

    def _tick(self) -> None:
        self._pulse += self._pulse_dir * 0.07
        if self._pulse >= 1.0:
            self._pulse = 1.0
            self._pulse_dir = -1
        elif self._pulse <= 0.0:
            self._pulse = 0.0
            self._pulse_dir = 1
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(self._BTN_W, self._BTN_H)
