"""BotonEra – entry point."""
import os
import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import QApplication

from src.main_window import MainWindow
from src.styles.theme import STYLESHEET

BASE_DIR = Path(__file__).parent


def main() -> None:
    # High-DPI: Qt6 has it on by default, but we pin the rounding policy
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("BotonEra")
    app.setOrganizationName("BotonEra")

    # Global font
    app.setFont(QFont("Segoe UI", 10))

    # App icon
    icon_path = str(BASE_DIR / "assets" / "logo.svg")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Apply global stylesheet
    app.setStyleSheet(STYLESHEET)

    window = MainWindow(BASE_DIR)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
