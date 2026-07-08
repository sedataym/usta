from PySide6.QtWidgets import QFontComboBox, QHBoxLayout, QLabel, QPushButton, QSpinBox, QVBoxLayout, QWidget

from src.i18n import _


def build_appearance_tab(panel):
    tab_appearance = QWidget()
    tab_appearance_layout = QVBoxLayout(tab_appearance)

    h_font = QHBoxLayout()
    v_font_family = QVBoxLayout()
    v_font_family.addWidget(QLabel(_("Font Family:")))
    panel.font_picker = QFontComboBox()
    panel.font_picker.currentFontChanged.connect(panel.on_font_changed)
    v_font_family.addWidget(panel.font_picker)
    h_font.addLayout(v_font_family)

    v_font_size = QVBoxLayout()
    v_font_size.addWidget(QLabel(_("Size:")))
    panel.font_size_spin = QSpinBox()
    panel.font_size_spin.setRange(8, 72)
    panel.font_size_spin.setValue(panel.overlay.font_size)
    panel.font_size_spin.valueChanged.connect(panel.on_font_size_changed)
    v_font_size.addWidget(panel.font_size_spin)
    h_font.addLayout(v_font_size)
    tab_appearance_layout.addLayout(h_font)

    h_colors = QHBoxLayout()
    panel.btn_color = QPushButton(_("🎨 Text Color"))
    panel.btn_color.clicked.connect(panel.choose_color)
    h_colors.addWidget(panel.btn_color)

    panel.color_sample = QLabel()
    panel.color_sample.setFixedSize(24, 24)
    panel.color_sample.setStyleSheet(f"background-color: {panel.overlay.font_color}; border: 1px solid gray; border-radius: 4px;")
    h_colors.addWidget(panel.color_sample)

    panel.btn_bg_color = QPushButton(_("🎨 Background"))
    panel.btn_bg_color.clicked.connect(panel.choose_bg_color)
    h_colors.addWidget(panel.btn_bg_color)

    panel.bg_color_sample = QLabel()
    panel.bg_color_sample.setFixedSize(24, 24)
    panel.bg_color_sample.setStyleSheet(f"background-color: {panel.overlay.bg_color}; border: 1px solid gray; border-radius: 4px;")
    h_colors.addWidget(panel.bg_color_sample)
    tab_appearance_layout.addLayout(h_colors)

    h_bg_opacity = QHBoxLayout()
    h_bg_opacity.addWidget(QLabel(_("Background Opacity:")))
    panel.bg_opacity_spin = QSpinBox()
    panel.bg_opacity_spin.setRange(0, 255)
    panel.bg_opacity_spin.setValue(panel.overlay.bg_opacity)
    panel.bg_opacity_spin.valueChanged.connect(panel.on_bg_opacity_changed)
    h_bg_opacity.addWidget(panel.bg_opacity_spin)
    tab_appearance_layout.addLayout(h_bg_opacity)
    tab_appearance_layout.addStretch()
    return tab_appearance
