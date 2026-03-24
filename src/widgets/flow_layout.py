"""FlowLayout – wraps children like text, left-to-right then onto the next row."""
from __future__ import annotations

from PyQt6.QtCore import QPoint, QRect, QSize, Qt
from PyQt6.QtWidgets import QLayout, QLayoutItem, QSizePolicy, QWidget


class FlowLayout(QLayout):
    def __init__(self, parent: QWidget | None = None, h_gap: int = 12, v_gap: int = 12) -> None:
        super().__init__(parent)
        self._h_gap = h_gap
        self._v_gap = v_gap
        self._items: list[QLayoutItem] = []

    # ── QLayout interface ───────────────────────────────────────────────────

    def addItem(self, item: QLayoutItem) -> None:            # noqa: N802
        self._items.append(item)

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int) -> QLayoutItem | None:      # noqa: N802
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index: int) -> QLayoutItem | None:      # noqa: N802
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def hasHeightForWidth(self) -> bool:                     # noqa: N802
        return True

    def heightForWidth(self, width: int) -> int:             # noqa: N802
        return self._do_layout(QRect(0, 0, width, 0), dry_run=True)

    def setGeometry(self, rect: QRect) -> None:              # noqa: N802
        super().setGeometry(rect)
        self._do_layout(rect, dry_run=False)

    def sizeHint(self) -> QSize:                             # noqa: N802
        return self.minimumSize()

    def minimumSize(self) -> QSize:                          # noqa: N802
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        return size + QSize(m.left() + m.right(), m.top() + m.bottom())

    def expandingDirections(self) -> Qt.Orientation:         # noqa: N802
        return Qt.Orientation(0)

    # ── Layout engine ───────────────────────────────────────────────────────

    def _do_layout(self, rect: QRect, *, dry_run: bool) -> int:
        m = self.contentsMargins()
        eff = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())

        x, y = eff.x(), eff.y()
        row_h = 0

        for item in self._items:
            # Skip hidden widgets — they take no space
            w = item.widget()
            if w is not None and not w.isVisible():
                continue

            hint = item.sizeHint()
            next_x = x + hint.width() + self._h_gap

            if next_x - self._h_gap > eff.right() and row_h > 0:
                x = eff.x()
                y += row_h + self._v_gap
                next_x = x + hint.width() + self._h_gap
                row_h = 0

            if not dry_run:
                item.setGeometry(QRect(QPoint(x, y), hint))

            x = next_x
            row_h = max(row_h, hint.height())

        return y + row_h - eff.y()
