from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QDoubleSpinBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from src.config import DPI_SCALE_DEFAULT, OCR_ENGINES, SCREENSHOT_ENGINES
from src.i18n import _


def build_ocr_tab(panel):
    tab_ocr = QWidget()
    tab_ocr_layout = QVBoxLayout(tab_ocr)
    tab_ocr_layout.addWidget(QLabel(_("OCR Engine:")))
    panel.combo_ocr = QComboBox()
    panel.combo_ocr.setFocusPolicy(Qt.NoFocus)
    panel.combo_ocr.addItems(OCR_ENGINES)
    panel.combo_ocr.currentTextChanged.connect(panel.worker.set_engine)
    panel.combo_ocr.currentTextChanged.connect(panel.save_settings)
    tab_ocr_layout.addWidget(panel.combo_ocr)

    tab_ocr_layout.addWidget(QLabel(_("Screen Engine:")))
    panel.combo_screenshot = QComboBox()
    panel.combo_screenshot.setFocusPolicy(Qt.NoFocus)
    panel.combo_screenshot.addItems(SCREENSHOT_ENGINES)
    panel.combo_screenshot.setCurrentText("Portal")
    panel.combo_screenshot.currentTextChanged.connect(panel.worker.set_screenshot_engine)
    panel.combo_screenshot.currentTextChanged.connect(panel.save_settings)
    tab_ocr_layout.addWidget(panel.combo_screenshot)

    panel.dpi_locked = False
    h_dpi = QHBoxLayout()
    h_dpi.addWidget(QLabel(_("DPI Scale:")))
    panel.dpi_lock_label = QLabel("🔓")
    panel.dpi_lock_label.setToolTip(_("DPI unlocked (click to lock)"))
    panel.dpi_lock_label.setCursor(Qt.PointingHandCursor)
    panel.dpi_lock_label.mousePressEvent = panel._toggle_dpi_lock
    panel.dpi_lock_label.setStyleSheet("font-size: 16px; padding: 0px;")
    panel.dpi_lock_label.setFixedWidth(24)
    h_dpi.addWidget(panel.dpi_lock_label)
    panel.dpi_scale_spin = QDoubleSpinBox()
    panel.dpi_scale_spin.setRange(50, 300)
    panel.dpi_scale_spin.setSingleStep(25)
    panel.dpi_scale_spin.setDecimals(0)
    panel.dpi_scale_spin.setSuffix(" %")
    panel.dpi_scale_spin.setValue(DPI_SCALE_DEFAULT * 100)
    panel.dpi_scale_spin.setToolTip(_("Scale factor for high-DPI monitors.\nAuto-detected when selecting a region."))
    panel.dpi_scale_spin.valueChanged.connect(panel.on_dpi_scale_changed)
    h_dpi.addWidget(panel.dpi_scale_spin)
    tab_ocr_layout.addLayout(h_dpi)

    tab_ocr_layout.addStretch()
    return tab_ocr
