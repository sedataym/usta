"""Application actions consumed by views; the worker owns mutable engines."""
class ApplicationController:
    def __init__(self, worker):
        self.worker = worker

    @property
    def capture_rect(self):
        return self.worker.capture_rect

    @property
    def dpi_scale(self):
        return self.worker.dpi_scale

    @dpi_scale.setter
    def dpi_scale(self, value):
        self.worker.dpi_scale = value

    def set_rect(self, rect, dpi_scale=None):
        if dpi_scale is None:
            self.worker.set_rect(rect)
        else:
            self.worker.set_rect(rect, dpi_scale)

    def set_engine(self, name):
        self.worker.set_engine(name)

    def set_translator(self, name):
        self.worker.set_translator(name)

    def set_screenshot_engine(self, name):
        self.worker.set_screenshot_engine(name)

    def set_languages(self, source, target):
        self.worker.set_languages(source, target)

    def set_api_key(self, engine, key):
        self.worker.set_api_key(engine, key)

    def is_running(self):
        return self.worker.isRunning()

    def start(self):
        self.worker.start()

    def stop(self):
        self.worker.stop()
