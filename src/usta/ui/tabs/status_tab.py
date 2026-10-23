from PySide6.QtGui import QFontDatabase
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

        self.timings_label = QLabel()
        self.timings_label.setWordWrap(False)
        self.timings_label.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        self.timings_label.setToolTip(_("Total includes screen capture and preprocessing."))
        self.reset_timings()
        tab_status_layout.addWidget(self.timings_label)

        self.rect_label_status = QLabel(_("Region: —"))
        self.rect_label_status.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        tab_status_layout.addWidget(self.rect_label_status)

    def _set_timings_text(self, ocr, translation, total):
        self.timings_label.setText(
            _("OCR: {ocr} s | Translation: {translation} s | Total: {total} s").format(
                ocr=ocr, translation=translation, total=total
            )
        )

    def update_timings(self, timings):
        self._set_timings_text(
            f"{timings.ocr_seconds:.2f}",
            f"{timings.translation_seconds:.2f}",
            f"{timings.total_seconds:.2f}",
        )

    def reset_timings(self):
        self._set_timings_text("—", "—", "—")
