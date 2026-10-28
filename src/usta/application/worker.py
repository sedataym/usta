"""Qt signals and thread lifecycle around the application pipeline."""

from dataclasses import replace

from PySide6.QtCore import QRect, QThread, Signal, Slot

from usta.application.pipeline import Pipeline
from usta.core.screenshot import ImageProcessor, ScreenshotFactory
from usta.infrastructure.paths import CaptureWorkspace
from usta.infrastructure.socket_publisher import TranslationPublisher


class OCRWorker(QThread):
    LOOP_SLEEP_SECONDS = Pipeline.LOOP_SLEEP_SECONDS
    new_translation = Signal(str)
    performance_update = Signal(float)
    timings_update = Signal(object)
    translation_status = Signal(bool)
    running_status = Signal(bool)
    error_occurred = Signal(str)
    _translation_ready = Signal(object)
    _error_ready = Signal(object)
    _timings_ready = Signal(object)

    def __init__(self):
        super().__init__()
        self.workspace = CaptureWorkspace()
        self.pipeline = Pipeline(
            capture_factory=lambda name: ScreenshotFactory.get_engine(
                name, self.workspace.fullscreen_path
            ),
            publisher=TranslationPublisher(),
            image_path=self.workspace.image_path,
            on_translation=self._queue_translation,
            on_error=self._queue_error,
            on_performance=self.performance_update.emit,
            on_timings=self._queue_timings,
            on_translating=self.translation_status.emit,
            rect_factory=lambda values: QRect(*values),
            preprocess=ImageProcessor.preprocess_for_tesseract,
        )
        self._translation_ready.connect(self._deliver_translation)
        self._error_ready.connect(self._deliver_error)
        self._timings_ready.connect(self._deliver_timings)
        self._restart_requested = False
        self.finished.connect(self._restart_if_requested)

    def _queue_translation(self, text):
        self._translation_ready.emit((self.pipeline.session_id, text))

    def _queue_error(self, text):
        self._error_ready.emit((self.pipeline.session_id, text))

    def _queue_timings(self, timings):
        self._timings_ready.emit((self.pipeline.session_id, timings))

    @Slot(object)
    def _deliver_timings(self, payload):
        session, timings = payload
        if self.pipeline.is_current(session):
            self.timings_update.emit(timings)

    @Slot(object)
    def _deliver_translation(self, payload):
        session, text = payload
        if self.pipeline.is_current(session):
            self.new_translation.emit(text)

    @Slot(object)
    def _deliver_error(self, payload):
        session, text = payload
        # Fatal capture errors belong to the just-stopped session as well.
        if session == self.pipeline.session_id:
            self.error_occurred.emit(text)

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
        self.pipeline.configure(
            replace(
                settings,
                capture_rect=(qrect.x(), qrect.y(), qrect.width(), qrect.height()),
                dpi_scale=settings.dpi_scale if dpi_scale is None else dpi_scale,
            )
        )

    def set_engine(self, name):
        self.pipeline.configure(replace(self.pipeline.settings, ocr_engine=name))

    def set_translator(self, name):
        self.pipeline.configure(replace(self.pipeline.settings, translator_engine=name))

    def set_screenshot_engine(self, name):
        self.pipeline.configure(replace(self.pipeline.settings, screenshot_engine=name))

    def set_languages(self, source, target):
        self.pipeline.configure(
            replace(self.pipeline.settings, source_lang=source, target_lang=target)
        )

    def set_api_key(self, engine, key):
        keys = self.pipeline.settings.translator_api_keys
        keys[engine] = key
        self.pipeline.configure(replace(self.pipeline.settings, translator_api_keys=keys))

    def start(self):
        if self.isRunning():
            self._restart_requested = self.pipeline.is_stopped
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
