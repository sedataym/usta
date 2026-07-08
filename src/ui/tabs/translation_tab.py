from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from src.config import LANGUAGES, TRANSLATION_ENGINES
from src.i18n import _


def build_translation_tab(panel):
    tab_translation = QWidget()
    tab_translation_layout = QVBoxLayout(tab_translation)
    tab_translation_layout.addWidget(QLabel(_("Translation Engine:")))
    panel.combo_translator = QComboBox()
    panel.combo_translator.setFocusPolicy(Qt.NoFocus)
    panel.combo_translator.addItems(TRANSLATION_ENGINES)
    panel.combo_translator.currentTextChanged.connect(panel.worker.set_translator)
    panel.combo_translator.currentTextChanged.connect(panel.save_settings)
    panel.combo_translator.currentTextChanged.connect(panel.on_translator_changed)
    tab_translation_layout.addWidget(panel.combo_translator)

    h_lang = QHBoxLayout()
    v_source = QVBoxLayout()
    v_source.addWidget(QLabel(_("Source Language:")))
    panel.combo_source = QComboBox()
    panel.combo_source.setFocusPolicy(Qt.NoFocus)
    panel.combo_source.addItems(list(LANGUAGES.keys()))
    panel.combo_source.setCurrentText("English")
    panel.combo_source.currentTextChanged.connect(panel.update_languages)
    v_source.addWidget(panel.combo_source)
    h_lang.addLayout(v_source)

    v_target = QVBoxLayout()
    v_target.addWidget(QLabel(_("Target Language:")))
    panel.combo_target = QComboBox()
    panel.combo_target.setFocusPolicy(Qt.NoFocus)
    panel.combo_target.addItems(list(LANGUAGES.keys()))
    panel.combo_target.setCurrentText("Turkish")
    panel.combo_target.currentTextChanged.connect(panel.update_languages)
    v_target.addWidget(panel.combo_target)
    h_lang.addLayout(v_target)
    tab_translation_layout.addLayout(h_lang)

    panel.api_key_label = QLabel(_("API Key"))
    tab_translation_layout.addWidget(panel.api_key_label)
    panel.api_key_input = QLineEdit()
    panel.api_key_input.setEchoMode(QLineEdit.Password)
    panel.api_key_input.setPlaceholderText(_("Enter API key..."))
    panel.api_key_input.textChanged.connect(panel.on_api_key_changed)
    tab_translation_layout.addWidget(panel.api_key_input)
    panel.api_keys = {}

    tab_translation_layout.addStretch()
    return tab_translation
