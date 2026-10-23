from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from usta.i18n import _


class StatusTab(QWidget):
    def __init__(self):
        super().__init__()
        tab_status_layout = QVBoxLayout(self)
        tab_status_layout.setSpacing(6)
        tab_status_layout.setContentsMargins(8, 8, 8, 8)

        h_system = QHBoxLayout()
        h_system.setSpacing(6)
        self.system_indicator = QLabel()
        self.system_indicator.setFixedSize(16, 16)
        self.system_indicator.setStyleSheet("background-color: #C62828; border-radius: 8px;")
        h_system.addWidget(self.system_indicator)
        self.system_status_label = QLabel(_("Stopped"))
        h_system.addWidget(self.system_status_label)
        h_system.addStretch()
        tab_status_layout.addLayout(h_system)

        tab_status_layout.addStretch()

        self.rect_label_status = QLabel(_("Region: —"))
        self.rect_label_status.setStyleSheet("font-family: monospace;")
        tab_status_layout.addWidget(self.rect_label_status)
