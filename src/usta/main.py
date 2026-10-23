import os
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from usta.config import OS
from usta.i18n import init_i18n
from usta.infrastructure.logging_setup import configure_logging
from usta.infrastructure.paths import prepare_paths, resolve_paths
from usta.ui.main_window import ControlPanel


def main():
    configure_logging()
    prepare_paths(resolve_paths())
    # Initialize internationalization
    init_i18n()

    if OS == "Linux":
        os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Set application icon
    icon_path = os.path.join(os.path.dirname(__file__), "ui", "assets", "usta.png")
    app.setWindowIcon(QIcon(icon_path))

    app.control_panel = ControlPanel()  # Retain the top-level widget for the event loop.
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
