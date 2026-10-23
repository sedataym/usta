import sys
from usta.core.registry import LazyEngines, OCR_FACTORIES
from usta.application.results import OCRResult

class OCRManager:
    def __init__(self):
        self.language = 'en'
        factories = {name: spec for name, spec in OCR_FACTORIES.items() if name != 'Apple Vision' or sys.platform == 'darwin'}
        self.engines = LazyEngines(factories, lambda name, engine: engine.set_language(self.language))
        self.current_engine_name = 'RapidOCR'

    def set_engine(self, name: str):
        if name in self.engines:
            self.current_engine_name = name

    def set_language(self, lang_code: str):
        self.language = lang_code
        for engine in self.engines.instances.values():
            engine.set_language(lang_code)

    def read_text(self, image_path: str) -> str:
        return self.engines[self.current_engine_name].read_text(image_path)

    def read_result(self, image_path: str) -> OCRResult:
        return OCRResult(self.read_text(image_path))
