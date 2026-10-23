import logging
import subprocess
import re
from usta.core.ocr.base_ocr import BaseOCREngine
from usta.config import OCR_LANG_MAPPING

logger = logging.getLogger(__name__)

class TesseractEngine(BaseOCREngine):
    def __init__(self):
        self.lang = "eng"

    def set_language(self, lang_code: str):
        mapping = OCR_LANG_MAPPING.get(lang_code, OCR_LANG_MAPPING["en"])
        self.lang = mapping["tess"]
        logger.info(f"TesseractEngine: Language set to {self.lang}")

    def read_text(self, image_path: str) -> str:
        cfg = [
            "tesseract", image_path, "stdout", 
            "--oem", "1", "--psm", "3", "-l", self.lang
        ]
        
        # Only add whitelist for English to avoid breaking other languages
        if self.lang == "eng":
            cfg.extend(["-c", "tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,!?'\"- "])

        try:
            result = subprocess.run(cfg, capture_output=True, text=True, check=True, timeout=15)
            text = result.stdout
            
            # Use a more inclusive regex that allows non-Latin characters
            # This allows common punctuation and spaces, plus any word character (including non-Latin)
            clean = re.sub(r'[^\w\s.,!?\'\"\-\(\)]', '', text, flags=re.UNICODE)
            return " ".join(clean.split()).strip()
        except Exception as e:
            logger.error(f"Tesseract Error: {e}")
            return ""
