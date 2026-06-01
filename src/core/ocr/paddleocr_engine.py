from src.core.ocr.base_ocr import BaseOCREngine
from src.config import OCR_LANG_MAPPING


class PaddleOCREngine(BaseOCREngine):
    def __init__(self):
        self.ocr = None
        self.current_lang = "en"
        self._unavailable_reason = None

    def set_language(self, lang_code: str):
        mapping = OCR_LANG_MAPPING.get(lang_code, OCR_LANG_MAPPING["en"])
        new_lang = mapping["paddle"]

        if new_lang != self.current_lang:
            self.current_lang = new_lang
            self.ocr = None  # Trigger re-initialization on next read
            self._unavailable_reason = None
            print(f"PaddleOCREngine: Language scheduled for update: {self.current_lang}")

    def read_text(self, image_path: str) -> str:
        if self.ocr is None and self._unavailable_reason is None:
            try:
                from paddleocr import PaddleOCR
                print(f"PaddleOCREngine: Initializing reader with lang={self.current_lang}")
                self.ocr = PaddleOCR(
                    lang=self.current_lang,
                    use_textline_orientation=True,
                )
            except ImportError as e:
                self._unavailable_reason = (
                    "PaddleOCR is not installed. "
                    "Install it with: pip install paddleocr\n"
                    "Note: PaddleOCR also requires paddlepaddle, which may not be "
                    "available for all Python versions (requires Python ≤ 3.12)."
                )
                print(f"PaddleOCREngine: {self._unavailable_reason}")
                return ""
            except RuntimeError as e:
                self._unavailable_reason = (
                    f"PaddleOCR runtime error: {e}\n"
                    "PaddleOCR requires paddlepaddle to be installed separately. "
                    "See https://www.paddlepaddle.org.cn/en for installation instructions. "
                    "Note: paddlepaddle may not support your current Python version."
                )
                print(f"PaddleOCREngine: {self._unavailable_reason}")
                return ""
            except Exception as e:
                self._unavailable_reason = f"PaddleOCR initialization failed: {e}"
                print(f"PaddleOCREngine: {self._unavailable_reason}")
                return ""

        if self._unavailable_reason:
            return ""

        try:
            result = self.ocr.ocr(image_path)
            if not result or not result[0]:
                return ""

            # Extract recognized text from all detected regions
            lines = []
            for line_group in result[0]:
                text = line_group[1][0]  # (bbox, (text, confidence))
                confidence = line_group[1][1]
                if text and confidence > 0.2:  # Filter low-confidence detections
                    lines.append(text)

            clean = " ".join(lines)
            return " ".join(clean.split()).strip()
        except Exception as e:
            print(f"PaddleOCR Error: {e}")
            return ""
