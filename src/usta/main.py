import sys
import os

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from usta.config import OS
from usta.ui.main_window import ControlPanel
from usta.i18n import init_i18n

def main():
    # Initialize internationalization
    init_i18n()
    
    if OS == "Linux":
        os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Set application icon
    icon_path = os.path.join(os.path.dirname(__file__), "ui", "assets", "usta.png")
    app.setWindowIcon(QIcon(icon_path))
    
    panel = ControlPanel()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
