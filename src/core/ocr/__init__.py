"""Pluggable OCR subsystem for Avos."""

from src.core.ocr.base_ocr import BaseOCREngine, OCRResult
from src.core.ocr.easyocr_engine import EasyOCREngine
from src.core.ocr.ocr_manager import OCRManager
from src.core.ocr.paddleocr_engine import PaddleOCREngine
from src.core.ocr.tesseract_engine import TesseractEngine

__all__ = [
    "BaseOCREngine",
    "EasyOCREngine",
    "OCRManager",
    "OCRResult",
    "PaddleOCREngine",
    "TesseractEngine",
]
