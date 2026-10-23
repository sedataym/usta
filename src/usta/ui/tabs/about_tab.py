from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from usta.config import APP_VERSION
from usta.i18n import _


from PySide6.QtCore import Signal


class AboutTab(QWidget):

    def __init__(self):
        super().__init__()
        tab_about_layout = QVBoxLayout(self)
        about_title = QLabel(_("<b>Universal Screen Translator Application</b>"))
        about_title.setStyleSheet("font-size: 14px;")
        tab_about_layout.addWidget(about_title)
        tab_about_layout.addWidget(QLabel(_("Version: {version}").format(version=APP_VERSION)))
        tab_about_layout.addWidget(QLabel(""))
        tab_about_layout.addWidget(QLabel(_("A real-time OCR-based translation tool.")))
        tab_about_layout.addWidget(QLabel(_("Select a screen region, capture text via OCR,")))
        tab_about_layout.addWidget(QLabel(_("and translate instantly with Google or DeepL.")))
        tab_about_layout.addStretch()
