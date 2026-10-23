from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from usta.config import LANGUAGES, TRANSLATION_ENGINES
from usta.i18n import _


from PySide6.QtCore import Signal


class TranslationTab(QWidget):
    translator_changed = Signal(str)
    changed = Signal()
    translator_selected = Signal(str)
    language_changed = Signal()
    api_key_changed = Signal(str)

    def __init__(self):
        super().__init__()
        tab_translation_layout = QVBoxLayout(self)
        tab_translation_layout.addWidget(QLabel(_("Translation Engine:")))
        self.combo_translator = QComboBox()
        self.combo_translator.setFocusPolicy(Qt.NoFocus)
        self.combo_translator.addItems(TRANSLATION_ENGINES)
        self.combo_translator.currentTextChanged.connect(self.translator_changed.emit)
        self.combo_translator.currentTextChanged.connect(self.changed.emit)
        self.combo_translator.currentTextChanged.connect(self.translator_selected.emit)
        tab_translation_layout.addWidget(self.combo_translator)
    
        h_lang = QHBoxLayout()
        v_source = QVBoxLayout()
        v_source.addWidget(QLabel(_("Source Language:")))
        self.combo_source = QComboBox()
        self.combo_source.setFocusPolicy(Qt.NoFocus)
        self.combo_source.addItems(list(LANGUAGES.keys()))
        self.combo_source.setCurrentText("English")
        self.combo_source.currentTextChanged.connect(self.language_changed.emit)
        v_source.addWidget(self.combo_source)
        h_lang.addLayout(v_source)
    
        v_target = QVBoxLayout()
        v_target.addWidget(QLabel(_("Target Language:")))
        self.combo_target = QComboBox()
        self.combo_target.setFocusPolicy(Qt.NoFocus)
        self.combo_target.addItems(list(LANGUAGES.keys()))
        self.combo_target.setCurrentText("Turkish")
        self.combo_target.currentTextChanged.connect(self.language_changed.emit)
        v_target.addWidget(self.combo_target)
        h_lang.addLayout(v_target)
        tab_translation_layout.addLayout(h_lang)
    
        self.api_key_label = QLabel(_("API Key"))
        tab_translation_layout.addWidget(self.api_key_label)
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText(_("Enter API key..."))
        self.api_key_input.textChanged.connect(self.api_key_changed.emit)
        tab_translation_layout.addWidget(self.api_key_input)
    
        tab_translation_layout.addStretch()
