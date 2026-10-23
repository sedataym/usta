from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QDoubleSpinBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from usta.config import DPI_SCALE_DEFAULT, OCR_ENGINES, SCREENSHOT_ENGINES
from usta.i18n import _


from PySide6.QtCore import Signal


class OCRTab(QWidget):
    engine_changed = Signal(str)
    screen_engine_changed = Signal(str)
    changed = Signal()
    dpi_changed = Signal(float)
    toggle_dpi_requested = Signal(object)

    def __init__(self):
        super().__init__()
        tab_ocr_layout = QVBoxLayout(self)
        tab_ocr_layout.addWidget(QLabel(_("OCR Engine:")))
        self.combo_ocr = QComboBox()
        self.combo_ocr.setFocusPolicy(Qt.NoFocus)
        self.combo_ocr.addItems(OCR_ENGINES)
        self.combo_ocr.currentTextChanged.connect(self.engine_changed.emit)
        self.combo_ocr.currentTextChanged.connect(self.changed.emit)
        tab_ocr_layout.addWidget(self.combo_ocr)
    
        tab_ocr_layout.addWidget(QLabel(_("Screen Engine:")))
        self.combo_screenshot = QComboBox()
        self.combo_screenshot.setFocusPolicy(Qt.NoFocus)
        self.combo_screenshot.addItems(SCREENSHOT_ENGINES)
        if SCREENSHOT_ENGINES:
            self.combo_screenshot.setCurrentText(SCREENSHOT_ENGINES[0])
        self.combo_screenshot.currentTextChanged.connect(self.screen_engine_changed.emit)
        self.combo_screenshot.currentTextChanged.connect(self.changed.emit)
        tab_ocr_layout.addWidget(self.combo_screenshot)
    
        h_dpi = QHBoxLayout()
        h_dpi.addWidget(QLabel(_("DPI Scale:")))
        self.dpi_lock_label = QLabel("🔓")
        self.dpi_lock_label.setToolTip(_("DPI unlocked (click to lock)"))
        self.dpi_lock_label.setCursor(Qt.PointingHandCursor)
        self.dpi_lock_label.mousePressEvent = self.toggle_dpi_requested.emit
        self.dpi_lock_label.setStyleSheet("font-size: 16px; padding: 0px;")
        self.dpi_lock_label.setFixedWidth(24)
        h_dpi.addWidget(self.dpi_lock_label)
        self.dpi_scale_spin = QDoubleSpinBox()
        self.dpi_scale_spin.setRange(50, 300)
        self.dpi_scale_spin.setSingleStep(25)
        self.dpi_scale_spin.setDecimals(0)
        self.dpi_scale_spin.setSuffix(" %")
        self.dpi_scale_spin.setValue(DPI_SCALE_DEFAULT * 100)
        self.dpi_scale_spin.setToolTip(_("Scale factor for high-DPI monitors.\nAuto-detected when selecting a region."))
        self.dpi_scale_spin.valueChanged.connect(self.dpi_changed.emit)
        h_dpi.addWidget(self.dpi_scale_spin)
        tab_ocr_layout.addLayout(h_dpi)
    
        tab_ocr_layout.addStretch()
