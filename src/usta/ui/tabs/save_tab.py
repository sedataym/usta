from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from usta.i18n import _


from PySide6.QtCore import Signal


class SaveTab(QWidget):
    save_requested = Signal()
    load_requested = Signal()
    delete_requested = Signal()

    def __init__(self):
        super().__init__()
        tab_save_layout = QVBoxLayout(self)
    
        h_name = QHBoxLayout()
        h_name.addWidget(QLabel(_("Preset Name:")))
        self.preset_name_input = QLineEdit()
        self.preset_name_input.setPlaceholderText(_("Enter preset name..."))
        h_name.addWidget(self.preset_name_input)
        tab_save_layout.addLayout(h_name)
    
        h_buttons = QHBoxLayout()
        self.btn_save_preset = QPushButton(_("💾 Save"))
        self.btn_save_preset.clicked.connect(self.save_requested.emit)
        h_buttons.addWidget(self.btn_save_preset)
    
        self.btn_load_preset = QPushButton(_("📂 Load"))
        self.btn_load_preset.clicked.connect(self.load_requested.emit)
        h_buttons.addWidget(self.btn_load_preset)
    
        self.btn_delete_preset = QPushButton(_("🗑 Delete"))
        self.btn_delete_preset.clicked.connect(self.delete_requested.emit)
        h_buttons.addWidget(self.btn_delete_preset)
        tab_save_layout.addLayout(h_buttons)
    
        tab_save_layout.addWidget(QLabel(_("Saved Presets:")))
        self.preset_combo = QComboBox()
        self.preset_combo.setFocusPolicy(Qt.NoFocus)
        tab_save_layout.addWidget(self.preset_combo)
        tab_save_layout.addStretch()
