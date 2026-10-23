"""Main/temporary capture-region state and its restoration timer."""

from PySide6.QtCore import QObject, QRect, QTimer, Signal


class RegionController(QObject):
    changed = Signal(str)

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.main_capture_rect = QRect(controller.capture_rect)
        self.main_dpi_scale = controller.dpi_scale
        self.temporary_active = False
        self.restore_timer = QTimer(self)
        self.restore_timer.setSingleShot(True)
        self.restore_timer.timeout.connect(self.restore_main_region)

    def apply_main_region(self, rect, dpi_scale=None):
        self.restore_timer.stop()
        self.temporary_active = False
        self.controller.set_rect(rect)
        if dpi_scale is not None:
            self.controller.dpi_scale = dpi_scale
        self.main_capture_rect = QRect(rect)
        self.main_dpi_scale = self.controller.dpi_scale
        self.changed.emit(f"Region: {rect.x()},{rect.y()} {rect.width()}x{rect.height()}")

    def apply_temporary_region(self, rect, dpi_scale=None):
        if not self.temporary_active:
            self.main_capture_rect = QRect(self.controller.capture_rect)
            self.main_dpi_scale = self.controller.dpi_scale
        self.controller.set_rect(rect)
        if dpi_scale is not None:
            self.controller.dpi_scale = dpi_scale
        self.temporary_active = True
        self.restore_timer.start(10_000)
        self.changed.emit(
            f"Temporary Region: {rect.x()},{rect.y()} {rect.width()}x{rect.height()} (10s)"
        )

    def restore_main_region(self):
        if self.temporary_active:
            self.apply_main_region(self.main_capture_rect, self.main_dpi_scale)
