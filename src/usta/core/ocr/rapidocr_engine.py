import logging
import glob
import os

from usta.core.ocr.base_ocr import BaseOCREngine
from usta.config import OCR_LANG_MAPPING

from usta.resource_paths import resource_path

logger = logging.getLogger(__name__)

_MODELS_DIR = str(resource_path("resources/ocr_models/rapidocr"))


class RapidOCREngine(BaseOCREngine):
    DEFAULT_CPU_THREADS = 1
    THREAD_ENV_VARS = (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "ORT_NUM_THREADS",
    )

    def __init__(self, cpu_threads: int = DEFAULT_CPU_THREADS):
        self.ocr = None
        self.current_lang = "en"
        self._unavailable_reason = None
        self.cpu_threads = max(1, int(cpu_threads))

    @staticmethod
    def _get_model_path(lang_code: str) -> str:
        if not lang_code or lang_code == "en":
            return ""

        pattern = os.path.join(_MODELS_DIR, f"{lang_code}_PP-OCR*.onnx")
        matches = sorted(glob.glob(pattern))
        if matches:
            logger.info(f"RapidOCREngine: Found recognition model for lang={lang_code}: {os.path.basename(matches[0])}")
            return matches[0]

        logger.info(f"RapidOCREngine: No recognition model found for lang={lang_code}, using default")
        return ""

    def set_language(self, lang_code: str):
        mapping = OCR_LANG_MAPPING.get(lang_code, OCR_LANG_MAPPING["en"])
        new_lang = mapping.get("rapid", mapping.get("paddle", "en"))

        if new_lang != self.current_lang:
            self.current_lang = new_lang
            self.ocr = None  # Trigger re-initialization on next read
            self._unavailable_reason = None
            logger.info(f"RapidOCREngine: Language scheduled for update: {self.current_lang}")

    def _apply_cpu_limit(self):
        thread_count = str(self.cpu_threads)
        for env_var in self.THREAD_ENV_VARS:
            os.environ.setdefault(env_var, thread_count)

    def _patch_rapidocr_ort_session(self):
        from usta.core.ocr.rapidocr_compat import patch_ort_session
        patch_ort_session(self.cpu_threads)

    def _initialize(self) -> bool:
        if self.ocr is not None:
            return True

        if self._unavailable_reason:
            return False

        try:
            self._apply_cpu_limit()

            from rapidocr_onnxruntime import RapidOCR

            self._patch_rapidocr_ort_session()

            logger.info(
                "RapidOCREngine: Initializing reader "
                f"with lang={self.current_lang}, cpu_threads={self.cpu_threads}, "
                "use_text_det=True, use_angle_cls=False"
            )
            rec_model_path = self._get_model_path(self.current_lang)

            self.ocr = RapidOCR(
                use_text_det=True,
                use_angle_cls=False,
                det_model_path="",
                det_limit_side_len=320,
                rec_model_path=rec_model_path,
                rec_batch_num=1,
            )
            return True
        except ImportError:
            self._unavailable_reason = (
                "RapidOCR is not installed. "
                "Install it with: pip install rapidocr-onnxruntime onnxruntime"
            )
            logger.info(f"RapidOCREngine: {self._unavailable_reason}")
            return False
        except Exception as e:
            self._unavailable_reason = f"RapidOCR initialization failed: {e}"
            logger.info(f"RapidOCREngine: {self._unavailable_reason}")
            return False

    def _extract_lines(self, result):
        if not result:
            return []

        # rapidocr-onnxruntime commonly returns (ocr_result, elapsed_time).
        if isinstance(result, tuple):
            result = result[0]

        # Some RapidOCR versions return an object with a result-like attribute.
        if hasattr(result, "txts"):
            return [text for text in result.txts if text]
        if hasattr(result, "texts"):
            return [text for text in result.texts if text]
        if hasattr(result, "result"):
            result = result.result

        lines = []
        for item in result or []:
            text = ""
            confidence = 1.0

            if isinstance(item, dict):
                text = item.get("text") or item.get("rec_text") or ""
                confidence = item.get("score", item.get("confidence", 1.0))
            elif isinstance(item, (list, tuple)):
                if len(item) >= 3 and isinstance(item[1], str):
                    # [box, text, confidence]
                    text = item[1]
                    confidence = item[2]
                elif len(item) >= 2 and isinstance(item[1], (list, tuple)):
                    # Paddle-like fallback: [box, [text, confidence]]
                    text = item[1][0] if item[1] else ""
                    confidence = item[1][1] if len(item[1]) > 1 else 1.0
                elif item and isinstance(item[0], str):
                    text = item[0]
                    confidence = item[1] if len(item) > 1 else 1.0

            try:
                confidence = float(confidence)
            except (TypeError, ValueError):
                confidence = 1.0

            if text and confidence > 0.2:
                lines.append(text)

        return lines

    def read_text(self, image_path: str) -> str:
        if not self._initialize():
            return ""

        try:
            result = self.ocr(image_path)
            lines = self._extract_lines(result)
            clean = " ".join(lines)
            return " ".join(clean.split()).strip().strip("_").rstrip(":")
        except Exception as e:
            logger.error(f"RapidOCR Error: {e}")
            return ""