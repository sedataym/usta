import sys

from usta.core.ocr.tesseract_engine import TesseractEngine
from usta.core.ocr.easyocr_engine import EasyOCREngine
from usta.core.ocr.paddleocr_engine import PaddleOCREngine
from usta.core.ocr.rapidocr_engine import RapidOCREngine
from usta.core.ocr.apple_vision_engine import AppleVisionEngine

class OCRManager:
    def __init__(self):
        self.engines = {
            "Tesseract": TesseractEngine(),
            "EasyOCR": EasyOCREngine(),
            "PaddleOCR": PaddleOCREngine(),
            "RapidOCR": RapidOCREngine()
        }
        if sys.platform == "darwin":
            self.engines["Apple Vision"] = AppleVisionEngine()
        self.current_engine_name = "RapidOCR"

    def set_engine(self, name: str):
        if name in self.engines:
            self.current_engine_name = name

    def set_language(self, lang_code: str):
        for engine in self.engines.values():
            engine.set_language(lang_code)

    def read_text(self, image_path: str) -> str:
        engine = self.engines.get(self.current_engine_name)
        if engine:
            return engine.read_text(image_path)
        return ""
