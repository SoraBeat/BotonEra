# BotonEra – color palette & global QSS stylesheet

# ── Palette ────────────────────────────────────────────────────────────────
BG         = "#0A0A0F"
BG_PANEL   = "#12121A"
BG_CARD    = "#1A1A26"
BG_CARD_HV = "#20203A"
BORDER     = "#2A2A3E"
BORDER_HV  = "#3A3A5A"

ACCENT_PURPLE = "#6C63FF"
ACCENT_CYAN   = "#00D9FF"
ACCENT_CORAL  = "#FF6B6B"
ACCENT_GREEN  = "#00FF88"

TEXT_PRIMARY   = "#E8E8F0"
TEXT_SECONDARY = "#6B6B8A"
TEXT_DIM       = "#3A3A5A"

# Button accent colours (cycled for new sounds)
BUTTON_COLORS = [
    "#6C63FF",  # purple
    "#00D9FF",  # cyan
    "#FF6B6B",  # coral
    "#FFD93D",  # amber
    "#6BCB77",  # green
    "#FF9A3C",  # orange
    "#C77DFF",  # violet
    "#4CC9F0",  # sky
    "#F72585",  # pink
    "#4361EE",  # cobalt
]

BUTTON_EMOJIS = ["🔊", "💥", "🎵", "🎤", "🥁", "🎸", "🔔", "💣", "🎺", "🎻"]

# ── Main QSS ───────────────────────────────────────────────────────────────
STYLESHEET = """
/* ── Base ── */
* {
    font-family: "Segoe UI", "Inter", "Arial", sans-serif;
    color: #E8E8F0;
    outline: none;
}

QMainWindow {
    background: #0A0A0F;
}

QWidget#central_widget {
    background: #0A0A0F;
}

/* ── Scroll area ── */
QScrollArea {
    background: transparent;
    border: none;
}

QScrollArea > QWidget > QWidget {
    background: transparent;
}

QScrollBar:vertical {
    background: #12121A;
    width: 6px;
    border-radius: 3px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #2A2A3E;
    border-radius: 3px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover {
    background: #6C63FF;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
    border: none;
}
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: none;
}

/* ── Header ── */
QWidget#header_bar {
    background: #12121A;
    border-bottom: 1px solid #2A2A3E;
}

QLabel#app_title {
    color: #E8E8F0;
    font-size: 17px;
    font-weight: 700;
    letter-spacing: 1px;
}

QLabel#section_label {
    color: #6B6B8A;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
}

/* ── ComboBox (device selectors) ── */
QComboBox {
    background: #1A1A26;
    color: #E8E8F0;
    border: 1px solid #2A2A3E;
    border-radius: 8px;
    padding: 5px 32px 5px 10px;
    font-size: 12px;
    min-width: 170px;
    max-width: 220px;
}
QComboBox:hover {
    border-color: #6C63FF;
    background: #1E1E30;
}
QComboBox:focus {
    border-color: #6C63FF;
}
QComboBox::drop-down {
    border: none;
    width: 28px;
    subcontrol-origin: padding;
    subcontrol-position: right center;
}
QComboBox::down-arrow {
    width: 0;
    height: 0;
}
QComboBox QAbstractItemView {
    background: #1A1A26;
    border: 1px solid #2A2A3E;
    border-radius: 8px;
    selection-background-color: #6C63FF40;
    selection-color: #E8E8F0;
    color: #E8E8F0;
    padding: 4px;
    outline: none;
}
QComboBox QAbstractItemView::item {
    padding: 6px 10px;
    border-radius: 6px;
    min-height: 28px;
}
QComboBox QAbstractItemView::item:hover {
    background: #6C63FF20;
}

/* ── Window control buttons ── */
QPushButton#btn_minimize,
QPushButton#btn_maximize,
QPushButton#btn_close {
    background: transparent;
    border: none;
    border-radius: 6px;
    font-size: 14px;
    min-width: 30px;
    max-width: 30px;
    min-height: 30px;
    max-height: 30px;
    color: #6B6B8A;
    padding: 0;
}
QPushButton#btn_minimize:hover,
QPushButton#btn_maximize:hover {
    background: #2A2A3E;
    color: #E8E8F0;
}
QPushButton#btn_close:hover {
    background: #FF6B6B30;
    color: #FF6B6B;
}
QPushButton#btn_minimize:pressed,
QPushButton#btn_maximize:pressed {
    background: #3A3A5A;
}
QPushButton#btn_close:pressed {
    background: #FF6B6B50;
}

/* ── Footer ── */
QWidget#footer_bar {
    background: #0E0E16;
    border-top: 1px solid #1E1E2E;
}

/* Stop All button */
QPushButton#stop_all_btn {
    background: #1E0D0D;
    color: #FF6B6B;
    border: 1px solid #FF6B6B35;
    border-radius: 8px;
    padding: 7px 16px;
    font-size: 12px;
    font-weight: 600;
}
QPushButton#stop_all_btn:hover {
    background: #2A1010;
    border-color: #FF6B6B80;
}
QPushButton#stop_all_btn:pressed {
    background: #FF6B6B20;
}

/* Volume slider */
QSlider#volume_slider::groove:horizontal {
    background: #2A2A3E;
    height: 4px;
    border-radius: 2px;
}
QSlider#volume_slider::handle:horizontal {
    background: #6C63FF;
    width: 14px;
    height: 14px;
    border-radius: 7px;
    margin: -5px 0;
    border: 2px solid #0A0A0F;
}
QSlider#volume_slider::handle:horizontal:hover {
    background: #8A82FF;
}
QSlider#volume_slider::sub-page:horizontal {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #6C63FF, stop:1 #00D9FF);
    border-radius: 2px;
}

QLabel#vol_label {
    color: #6B6B8A;
    font-size: 11px;
    min-width: 34px;
}

/* ── Dialog ── */
QDialog {
    background: #12121A;
}
QDialog QLabel {
    color: #E8E8F0;
}

QLineEdit {
    background: #1A1A26;
    color: #E8E8F0;
    border: 1px solid #2A2A3E;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
}
QLineEdit:focus {
    border-color: #6C63FF;
    background: #1E1E32;
}
QLineEdit:hover {
    border-color: #3A3A5A;
}
QLineEdit::placeholder {
    color: #3A3A5A;
}

QPushButton#ok_btn {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #6C63FF, stop:1 #00D9FF);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 9px 28px;
    font-size: 13px;
    font-weight: 600;
}
QPushButton#ok_btn:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #7D75FF, stop:1 #20E5FF);
}
QPushButton#ok_btn:pressed {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #5A52DD, stop:1 #00BDD9);
}

QPushButton#cancel_btn {
    background: #1A1A26;
    color: #6B6B8A;
    border: 1px solid #2A2A3E;
    border-radius: 8px;
    padding: 9px 28px;
    font-size: 13px;
}
QPushButton#cancel_btn:hover {
    color: #E8E8F0;
    border-color: #6B6B8A;
    background: #20203A;
}
QPushButton#cancel_btn:pressed {
    background: #16162A;
}

QPushButton#preview_btn {
    background: #1A1A26;
    color: #00D9FF;
    border: 1px solid #00D9FF40;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 12px;
}
QPushButton#preview_btn:hover {
    background: #00D9FF15;
    border-color: #00D9FF80;
}

/* Drop zone */
QLabel#drop_zone {
    background: #1A1A26;
    border: 2px dashed #2A2A3E;
    border-radius: 12px;
    color: #6B6B8A;
    font-size: 13px;
    qproperty-alignment: AlignCenter;
}

QPushButton#browse_btn {
    background: #1A1A26;
    color: #6C63FF;
    border: 1px solid #6C63FF40;
    border-radius: 8px;
    padding: 8px 20px;
    font-size: 12px;
    font-weight: 600;
}
QPushButton#browse_btn:hover {
    background: #6C63FF15;
    border-color: #6C63FF90;
}

/* Context menu */
QMenu {
    background: #1A1A26;
    border: 1px solid #2A2A3E;
    border-radius: 10px;
    padding: 6px;
    color: #E8E8F0;
    font-size: 12px;
}
QMenu::item {
    padding: 7px 18px 7px 12px;
    border-radius: 6px;
}
QMenu::item:selected {
    background: #6C63FF25;
    color: #E8E8F0;
}
QMenu::separator {
    height: 1px;
    background: #2A2A3E;
    margin: 4px 8px;
}

/* Tooltip */
QToolTip {
    background: #1A1A26;
    color: #E8E8F0;
    border: 1px solid #2A2A3E;
    border-radius: 6px;
    padding: 5px 8px;
    font-size: 11px;
}

/* ── Header add-sound button ── */
QPushButton#btn_add_sound {
    background: transparent;
    color: #E8E8F0;
    border: 1px solid rgba(108,99,255,0.38);
    border-radius: 6px;
    font-size: 18px;
    font-weight: 300;
    padding: 0;
}
QPushButton#btn_add_sound:hover {
    background: rgba(108,99,255,0.20);
    border-color: #6C63FF;
    color: #FFFFFF;
}
QPushButton#btn_add_sound:pressed {
    background: rgba(108,99,255,0.35);
}
"""
