from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase, QPalette
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLCDNumber,
    QVBoxLayout,
    QWidget,
)

from usta.i18n import _


class StatusTab(QWidget):
    def __init__(self):
        super().__init__()
        self._layout = QVBoxLayout(self)
        self._layout.setSpacing(6)
        self._layout.setContentsMargins(8, 8, 8, 8)

        h_system = QHBoxLayout()
        h_system.setSpacing(6)
        h_system.setContentsMargins(2, 0, 2, 0)
        self.system_indicator = QLabel()
        self.system_indicator.setFixedSize(8, 8)
        self.system_indicator.setStyleSheet("background-color: #C62828; border-radius: 4px;")
        h_system.addWidget(self.system_indicator)
        self.system_status_label = QLabel(_("Stopped"))
        status_font = self.system_status_label.font()
        status_font.setBold(True)
        self.system_status_label.setFont(status_font)
        h_system.addWidget(self.system_status_label)
        h_system.addStretch()
        self._layout.addLayout(h_system)
        self._layout.addStretch()

        self._metrics = QGridLayout()
        self._metrics.setContentsMargins(2, 0, 2, 0)
        self._metrics.setHorizontalSpacing(8)
        self._metrics.setVerticalSpacing(3)
        self._metrics.setColumnStretch(1, 1)
        self._layout.addLayout(self._metrics)
        self.ocr_value = self._add_timing_row(0, _("OCR"))
        self.translation_value = self._add_timing_row(1, _("Translation"))
        self.total_value = self._add_timing_row(2, _("Total"), total=True)
        self.total_value.setToolTip(_("Total includes screen capture and preprocessing."))
        self.reset_timings()

        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: palette(mid);")
        self._layout.addWidget(separator)
        region = QHBoxLayout()
        region.setContentsMargins(2, 0, 2, 0)
        region.addWidget(QLabel(_("Region")), alignment=Qt.AlignTop)
        region.addStretch()
        values = QVBoxLayout()
        values.setSpacing(2)
        number_font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        fixed_families = [
            family for family in QFontDatabase.families() if QFontDatabase.isFixedPitch(family)
        ]
        if number_font.family() not in fixed_families and fixed_families:
            preferred = ("Menlo", "DejaVu Sans Mono", "Liberation Mono", "Consolas")
            number_font.setFamily(
                next(
                    (family for family in preferred if family in fixed_families), fixed_families[0]
                )
            )
        number_font.setPointSize(10)
        self.region_position = QLabel("—")
        self.region_size = QLabel("—")
        for value in (self.region_position, self.region_size):
            value.setFont(number_font)
            value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            value.setTextInteractionFlags(Qt.TextSelectableByMouse)
            values.addWidget(value)
        region.addLayout(values)
        self._layout.addLayout(region)

    def _add_timing_row(self, row, title, total=False):
        caption = QLabel(title)
        font = caption.font()
        font.setBold(total)
        caption.setFont(font)
        self._metrics.addWidget(caption, row, 0)
        display = QLCDNumber()
        display.setFrameShape(QFrame.NoFrame)
        display.setSegmentStyle(QLCDNumber.Flat)
        display.setSmallDecimalPoint(True)
        display.setFixedSize(96, 20)
        display.setAccessibleName(title)
        if total:
            accent = display.palette()
            accent.setColor(QPalette.WindowText, accent.color(QPalette.Highlight))
            display.setPalette(accent)
            caption.setPalette(accent)
        self._metrics.addWidget(display, row, 2, alignment=Qt.AlignRight)
        unit = QLabel("s")
        unit_palette = unit.palette()
        unit_palette.setColor(
            QPalette.WindowText, unit_palette.color(QPalette.Disabled, QPalette.WindowText)
        )
        unit.setPalette(unit_palette)
        self._metrics.addWidget(unit, row, 3)
        return display

    def _set_timings_text(self, ocr, translation, total):
        for display, text in zip(
            (self.ocr_value, self.translation_value, self.total_value),
            (ocr, translation, total),
        ):
            display.setDigitCount(max(6, len(text.replace(".", ""))))
            display.display(text)
            display.setAccessibleDescription(f"{text} s" if text != "--.--" else "—")

    def update_timings(self, timings):
        self._set_timings_text(
            f"{timings.ocr_seconds:.2f}",
            f"{timings.translation_seconds:.2f}",
            f"{timings.total_seconds:.2f}",
        )

    def reset_timings(self):
        self._set_timings_text("--.--", "--.--", "--.--")

    def update_region(self, rect):
        self.region_position.setText(f"X {rect.x()}   Y {rect.y()}")
        self.region_size.setText(f"{rect.width()} × {rect.height()} px")
