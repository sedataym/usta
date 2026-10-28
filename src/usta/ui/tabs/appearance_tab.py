from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFontComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from usta.application.settings import AppSettings
from usta.i18n import _


class AppearanceTab(QWidget):
    font_changed = Signal(object)
    font_size_changed = Signal(int)
    text_color_requested = Signal()
    background_color_requested = Signal()
    opacity_changed = Signal(int)

    def __init__(self, settings=None):
        super().__init__()
        settings = settings or AppSettings()
        tab_appearance_layout = QVBoxLayout(self)

        h_font = QHBoxLayout()
        v_font_family = QVBoxLayout()
        v_font_family.addWidget(QLabel(_("Font Family:")))
        self.font_picker = QFontComboBox()
        self.font_picker.currentFontChanged.connect(self.font_changed.emit)
        v_font_family.addWidget(self.font_picker)
        h_font.addLayout(v_font_family)

        v_font_size = QVBoxLayout()
        v_font_size.addWidget(QLabel(_("Size:")))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 72)
        self.font_size_spin.setValue(settings.font_size)
        self.font_size_spin.valueChanged.connect(self.font_size_changed.emit)
        v_font_size.addWidget(self.font_size_spin)
        h_font.addLayout(v_font_size)
        tab_appearance_layout.addLayout(h_font)

        h_colors = QHBoxLayout()
        self.btn_color = QPushButton(_("🎨 Text Color"))
        self.btn_color.clicked.connect(self.text_color_requested)
        h_colors.addWidget(self.btn_color)

        self.color_sample = QLabel()
        self.color_sample.setFixedSize(24, 24)
        self.color_sample.setStyleSheet(
            f"background-color: {settings.font_color}; border: 1px solid gray; border-radius: 4px;"
        )
        h_colors.addWidget(self.color_sample)

        self.btn_bg_color = QPushButton(_("🎨 Background"))
        self.btn_bg_color.clicked.connect(self.background_color_requested)
        h_colors.addWidget(self.btn_bg_color)

        self.bg_color_sample = QLabel()
        self.bg_color_sample.setFixedSize(24, 24)
        self.bg_color_sample.setStyleSheet(
            f"background-color: {settings.bg_color}; border: 1px solid gray; border-radius: 4px;"
        )
        h_colors.addWidget(self.bg_color_sample)
        tab_appearance_layout.addLayout(h_colors)

        h_bg_opacity = QHBoxLayout()
        h_bg_opacity.addWidget(QLabel(_("Background Opacity:")))
        self.bg_opacity_spin = QSpinBox()
        self.bg_opacity_spin.setRange(0, 255)
        self.bg_opacity_spin.setValue(settings.bg_opacity)
        self.bg_opacity_spin.valueChanged.connect(self.opacity_changed.emit)
        h_bg_opacity.addWidget(self.bg_opacity_spin)
        tab_appearance_layout.addLayout(h_bg_opacity)
        tab_appearance_layout.addStretch()
