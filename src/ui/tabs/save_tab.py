from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from src.i18n import _


def build_save_tab(panel):
    tab_save = QWidget()
    tab_save_layout = QVBoxLayout(tab_save)

    h_name = QHBoxLayout()
    h_name.addWidget(QLabel(_("Preset Name:")))
    panel.preset_name_input = QLineEdit()
    panel.preset_name_input.setPlaceholderText(_("Enter preset name..."))
    h_name.addWidget(panel.preset_name_input)
    tab_save_layout.addLayout(h_name)

    h_buttons = QHBoxLayout()
    panel.btn_save_preset = QPushButton(_("💾 Save"))
    panel.btn_save_preset.clicked.connect(panel.save_preset)
    h_buttons.addWidget(panel.btn_save_preset)

    panel.btn_load_preset = QPushButton(_("📂 Load"))
    panel.btn_load_preset.clicked.connect(panel.load_preset)
    h_buttons.addWidget(panel.btn_load_preset)

    panel.btn_delete_preset = QPushButton(_("🗑 Delete"))
    panel.btn_delete_preset.clicked.connect(panel.delete_preset)
    h_buttons.addWidget(panel.btn_delete_preset)
    tab_save_layout.addLayout(h_buttons)

    tab_save_layout.addWidget(QLabel(_("Saved Presets:")))
    panel.preset_combo = QComboBox()
    panel.preset_combo.setFocusPolicy(Qt.NoFocus)
    tab_save_layout.addWidget(panel.preset_combo)
    tab_save_layout.addStretch()
    return tab_save
