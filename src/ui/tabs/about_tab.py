from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from src.config import APP_VERSION
from src.i18n import _


def build_about_tab(panel):
    tab_about = QWidget()
    tab_about_layout = QVBoxLayout(tab_about)
    about_title = QLabel(_("<b>Universal Screen Translator Application</b>"))
    about_title.setStyleSheet("font-size: 14px;")
    tab_about_layout.addWidget(about_title)
    tab_about_layout.addWidget(QLabel(_("Version: {version}").format(version=APP_VERSION)))
    tab_about_layout.addWidget(QLabel(""))
    tab_about_layout.addWidget(QLabel(_("A real-time OCR-based translation tool.")))
    tab_about_layout.addWidget(QLabel(_("Select a screen region, capture text via OCR,")))
    tab_about_layout.addWidget(QLabel(_("and translate instantly with Google or DeepL.")))
    tab_about_layout.addStretch()
    return tab_about
