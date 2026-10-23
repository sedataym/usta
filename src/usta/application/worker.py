"""Qt signals and thread lifecycle around the application pipeline."""
from dataclasses import replace
from PySide6.QtCore import QThread, Signal, QRect
from usta.application.pipeline import Pipeline
from usta.infrastructure.paths import CaptureWorkspace
from usta.core.screenshot import ScreenshotFactory, ImageProcessor
from usta.infrastructure.socket_publisher import TranslationPublisher

class OCRWorker(QThread):
    LOOP_SLEEP_SECONDS = Pipeline.LOOP_SLEEP_SECONDS
    new_translation = Signal(str)
    performance_update = Signal(float)
    translation_status = Signal(bool)
    running_status = Signal(bool)
    error_occurred = Signal(str)

    def __init__(self):
        super().__init__()
        self.workspace = CaptureWorkspace()
        self.pipeline = Pipeline(capture_factory=lambda name: ScreenshotFactory.get_engine(name, self.workspace.fullscreen_path),
            publisher=TranslationPublisher(), image_path=self.workspace.image_path,
            on_translation=self.new_translation.emit, on_error=self.error_occurred.emit,
            on_performance=self.performance_update.emit, on_translating=self.translation_status.emit,
            rect_factory=lambda values: QRect(*values), preprocess=ImageProcessor.preprocess_for_tesseract)
        self._restart_requested = False
        self.finished.connect(self._restart_if_requested)

    @property
    def capture_rect(self):
        return QRect(*self.pipeline.settings.capture_rect)

    @property
    def dpi_scale(self):
        return self.pipeline.settings.dpi_scale

    @dpi_scale.setter
    def dpi_scale(self, value):
        self.pipeline.configure(replace(self.pipeline.settings, dpi_scale=value))

    def set_rect(self, qrect, dpi_scale=None):
        settings = self.pipeline.settings
        self.pipeline.configure(replace(settings, capture_rect=(qrect.x(),qrect.y(),qrect.width(),qrect.height()),
            dpi_scale=settings.dpi_scale if dpi_scale is None else dpi_scale))

    def set_engine(self, name):
        self.pipeline.configure(replace(self.pipeline.settings, ocr_engine=name))

    def set_translator(self, name):
        self.pipeline.configure(replace(self.pipeline.settings, translator_engine=name))

    def set_screenshot_engine(self, name):
        self.pipeline.configure(replace(self.pipeline.settings, screenshot_engine=name))

    def set_languages(self, source, target):
        self.pipeline.configure(replace(self.pipeline.settings, source_lang=source, target_lang=target))

    def set_api_key(self, engine, key):
        keys = self.pipeline.settings.translator_api_keys
        keys[engine] = key
        self.pipeline.configure(replace(self.pipeline.settings, translator_api_keys=keys))

    def start(self):
        if self.isRunning():
            self._restart_requested = True
            return
        self.pipeline.start()
        super().start()

    def _restart_if_requested(self):
        if self._restart_requested:
            self._restart_requested = False
            self.start()

    def stop(self):
        self._restart_requested = False
        self.pipeline.stop()
        if not self.isRunning():
            self.running_status.emit(False)

    def close(self):
        self.stop()
        self.pipeline.close()
        self.workspace.close()

    def run(self):
        self.running_status.emit(True)
        try:
            self.pipeline.run()
        finally:
            self.running_status.emit(False)
