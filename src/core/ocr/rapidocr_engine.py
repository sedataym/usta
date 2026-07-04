import os

from src.core.ocr.base_ocr import BaseOCREngine
from src.config import OCR_LANG_MAPPING


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

    def set_language(self, lang_code: str):
        mapping = OCR_LANG_MAPPING.get(lang_code, OCR_LANG_MAPPING["en"])
        new_lang = mapping.get("rapid", mapping.get("paddle", "en"))

        if new_lang != self.current_lang:
            self.current_lang = new_lang
            self.ocr = None  # Trigger re-initialization on next read
            self._unavailable_reason = None
            print(f"RapidOCREngine: Language scheduled for update: {self.current_lang}")

    def _apply_cpu_limit(self):
        thread_count = str(self.cpu_threads)
        for env_var in self.THREAD_ENV_VARS:
            os.environ.setdefault(env_var, thread_count)

    def _patch_rapidocr_ort_session(self):
        from onnxruntime import GraphOptimizationLevel, InferenceSession, SessionOptions
        from rapidocr_onnxruntime.utils import OrtInferSession, get_available_providers, get_device

        cpu_threads = self.cpu_threads

        def limited_init(session_self, config):
            sess_opt = SessionOptions()
            sess_opt.log_severity_level = 4
            sess_opt.enable_cpu_mem_arena = False
            sess_opt.graph_optimization_level = GraphOptimizationLevel.ORT_ENABLE_ALL
            sess_opt.intra_op_num_threads = cpu_threads
            sess_opt.inter_op_num_threads = 1

            cpu_ep = "CPUExecutionProvider"
            cpu_provider_options = {
                "arena_extend_strategy": "kSameAsRequested",
                "intra_op_num_threads": str(cpu_threads),
            }

            cuda_ep = "CUDAExecutionProvider"
            cuda_provider_options = {
                "device_id": 0,
                "arena_extend_strategy": "kNextPowerOfTwo",
                "cudnn_conv_algo_search": "EXHAUSTIVE",
                "do_copy_in_default_stream": True,
            }

            ep_list = []
            if (
                config["use_cuda"]
                and get_device() == "GPU"
                and cuda_ep in get_available_providers()
            ):
                ep_list = [(cuda_ep, cuda_provider_options)]
            ep_list.append((cpu_ep, cpu_provider_options))

            session_self._verify_model(config["model_path"])
            session_self.session = InferenceSession(
                config["model_path"],
                sess_options=sess_opt,
                providers=ep_list,
            )

        if getattr(OrtInferSession.__init__, "_usta_cpu_limited", False):
            return

        limited_init._usta_cpu_limited = True
        OrtInferSession.__init__ = limited_init

    def _initialize(self) -> bool:
        if self.ocr is not None:
            return True

        if self._unavailable_reason:
            return False

        try:
            self._apply_cpu_limit()

            from rapidocr_onnxruntime import RapidOCR

            self._patch_rapidocr_ort_session()

            print(
                "RapidOCREngine: Initializing reader "
                f"with lang={self.current_lang}, cpu_threads={self.cpu_threads}, "
                "use_text_det=True, use_angle_cls=False"
            )
            self.ocr = RapidOCR(
                use_text_det=True,
                use_angle_cls=False,
                det_model_path="",
                det_limit_side_len=320,
                rec_model_path="",
                rec_batch_num=1,
            )
            return True
        except ImportError:
            self._unavailable_reason = (
                "RapidOCR is not installed. "
                "Install it with: pip install rapidocr-onnxruntime onnxruntime"
            )
            print(f"RapidOCREngine: {self._unavailable_reason}")
            return False
        except Exception as e:
            self._unavailable_reason = f"RapidOCR initialization failed: {e}"
            print(f"RapidOCREngine: {self._unavailable_reason}")
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
            print(f"RapidOCR Error: {e}")
            return ""
