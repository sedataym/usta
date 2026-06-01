from src.core.ocr.tesseract_engine import TesseractEngine
from src.core.ocr.easyocr_engine import EasyOCREngine
from src.core.ocr.paddleocr_engine import PaddleOCREngine

class OCRManager:
    def __init__(self):
        self.engines = {
            "Tesseract": TesseractEngine(),
            "EasyOCR": EasyOCREngine(),
            "PaddleOCR": PaddleOCREngine()
        }
        self.current_engine_name = "Tesseract"

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
