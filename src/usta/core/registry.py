"""Names and lazy engine factories; importing this module loads no backend."""

from collections.abc import Mapping
from importlib import import_module

OCR_FACTORIES = {
    "RapidOCR": ("usta.core.ocr.rapidocr_engine", "RapidOCREngine"),
    "Tesseract": ("usta.core.ocr.tesseract_engine", "TesseractEngine"),
    "EasyOCR": ("usta.core.ocr.easyocr_engine", "EasyOCREngine"),
    "PaddleOCR": ("usta.core.ocr.paddleocr_engine", "PaddleOCREngine"),
    "Apple Vision": ("usta.core.ocr.apple_vision_engine", "AppleVisionEngine"),
}
DEFAULT_OCR_NAMES = ["RapidOCR", "Tesseract", "EasyOCR"]
TRANSLATOR_FACTORIES = {
    "Google": ("usta.core.translation.google_engine", "GoogleEngine"),
    "DeepL": ("usta.core.translation.deepl_engine", "DeepLTranslatorEngine"),
}


class LazyEngines(Mapping):
    def __init__(self, factories, initialize):
        self.factories = factories
        self.initialize = initialize
        self.instances = {}

    def __getitem__(self, name):
        if name not in self.instances:
            module, class_name = self.factories[name]
            engine = getattr(import_module(module), class_name)()
            self.initialize(name, engine)
            self.instances[name] = engine
        return self.instances[name]

    def __contains__(self, name):
        return name in self.factories

    def __iter__(self):
        return iter(self.factories)

    def __len__(self):
        return len(self.factories)
