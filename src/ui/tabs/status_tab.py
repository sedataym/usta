from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from src.i18n import _


def build_status_tab(panel):
    tab_status = QWidget()
    tab_status_layout = QVBoxLayout(tab_status)
    tab_status_layout.setSpacing(6)
    tab_status_layout.setContentsMargins(8, 8, 8, 8)

    h_system = QHBoxLayout()
    h_system.setSpacing(6)
    panel.system_indicator = QLabel()
    panel.system_indicator.setFixedSize(16, 16)
    panel.system_indicator.setStyleSheet(
        "background-color: #C62828; border-radius: 8px;"
    )
    h_system.addWidget(panel.system_indicator)
    panel.system_status_label = QLabel("Stopped")
    h_system.addWidget(panel.system_status_label)
    h_system.addStretch()
    tab_status_layout.addLayout(h_system)

    tab_status_layout.addStretch()

    panel.rect_label_status = QLabel(_("Region: —"))
    panel.rect_label_status.setStyleSheet("font-family: monospace;")
    tab_status_layout.addWidget(panel.rect_label_status)

    return tab_status
