import os
import pickle

from src.config import CUSTOM_OCR_APIS_FILE
from src.core.ocr.custom_api_engine import CustomAPIOCREngine
from src.core.ocr.tesseract_engine import TesseractEngine
from src.core.ocr.easyocr_engine import EasyOCREngine
from src.core.ocr.paddleocr_engine import PaddleOCREngine
from src.core.ocr.rapidocr_engine import RapidOCREngine

class OCRManager:
    def __init__(self):
        self.builtin_engines = {
            "Tesseract": TesseractEngine(),
            "EasyOCR": EasyOCREngine(),
            "PaddleOCR": PaddleOCREngine(),
            "RapidOCR": RapidOCREngine()
        }
        self.engines = dict(self.builtin_engines)
        self.current_engine_name = "RapidOCR"
        self.reload_custom_engines()

    def _load_custom_api_configs(self):
        if not os.path.exists(CUSTOM_OCR_APIS_FILE):
            return {}
        try:
            with open(CUSTOM_OCR_APIS_FILE, "rb") as f:
                payload = pickle.load(f)
        except Exception as e:
            print(f"Custom OCR APIs load error: {e}")
            return {}

        if not isinstance(payload, dict):
            return {}
        return payload

    def reload_custom_engines(self):
        self.engines = dict(self.builtin_engines)
        configs = self._load_custom_api_configs()
        builtin_names = set(self.builtin_engines.keys())

        for raw_name, config in configs.items():
            name = str(raw_name).strip() if raw_name is not None else ""
            if not name or name in builtin_names or not isinstance(config, dict):
                continue
            endpoint = config.get("endpoint")
            if not isinstance(endpoint, str) or not endpoint.strip():
                continue
            headers = config.get("headers", {})
            if headers is None:
                headers = {}
            if not isinstance(headers, dict):
                continue
            self.engines[name] = CustomAPIOCREngine(name, endpoint.strip(), headers)

        if self.current_engine_name not in self.engines:
            self.current_engine_name = "RapidOCR" if "RapidOCR" in self.engines else next(iter(self.engines), "")

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
