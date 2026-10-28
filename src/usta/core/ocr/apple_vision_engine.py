"""On-device text recognition using macOS Vision through PyObjC."""

import logging
from pathlib import Path

from usta.core.ocr.base_ocr import BaseOCREngine

logger = logging.getLogger(__name__)


class AppleVisionEngine(BaseOCREngine):
    def __init__(self):
        self.language = "en"
        self._unavailable_reason = None
        self._warned_languages = set()

    def set_language(self, lang_code: str):
        self.language = lang_code or "auto"

    def _make_request(self, vision):
        request = vision.VNRecognizeTextRequest.alloc().init()
        request.setRecognitionLevel_(vision.VNRequestTextRecognitionLevelAccurate)
        request.setUsesLanguageCorrection_(True)
        supported, error = request.supportedRecognitionLanguagesAndReturnError_(None)
        if error is not None:
            raise RuntimeError(f"Vision language lookup failed: {error}")
        supported = [str(language) for language in supported or []]
        preferred = {"zh": "zh-Hans"}.get(self.language, self.language).replace("_", "-")
        selected = next(
            (language for language in supported if language.lower() == preferred.lower()), None
        )
        if selected is None:
            selected = next(
                (
                    language
                    for language in supported
                    if language.lower().startswith(preferred.lower() + "-")
                ),
                None,
            )
        automatic = preferred == "auto" or selected is None
        if automatic:
            languages = supported
            if preferred != "auto" and preferred not in self._warned_languages:
                logger.warning(
                    "Apple Vision does not support language %s on this macOS; "
                    "using automatic language detection",
                    self.language,
                )
                self._warned_languages.add(preferred)
        else:
            languages = [selected]
            if selected != "en-US" and "en-US" in supported:
                languages.append("en-US")
        if languages:
            request.setRecognitionLanguages_(languages)
        if hasattr(request, "setAutomaticallyDetectsLanguage_"):
            request.setAutomaticallyDetectsLanguage_(automatic)
        return request

    def read_text(self, image_path: str) -> str:
        if self._unavailable_reason:
            return ""
        try:
            import objc
            import Vision
            from Foundation import NSURL
        except ImportError as ex:
            self._unavailable_reason = str(ex)
            logger.error("Apple Vision requires macOS and pyobjc-framework-Vision: %s", ex)
            return ""

        try:
            # OCR runs on a QThread, so release each frame's Cocoa objects here.
            with objc.autorelease_pool():
                request = self._make_request(Vision)
                url = NSURL.fileURLWithPath_(str(Path(image_path).resolve()))
                handler = Vision.VNImageRequestHandler.alloc().initWithURL_options_(url, {})
                success, error = handler.performRequests_error_([request], None)
                if not success:
                    raise RuntimeError(str(error or "Vision request failed"))
                lines = []
                for observation in request.results() or []:
                    candidates = observation.topCandidates_(1)
                    if candidates:
                        lines.append(str(candidates[0].string()))
                return " ".join(" ".join(lines).split()).strip().strip("_").rstrip(":")
        except Exception as ex:
            logger.error("Apple Vision OCR failed: %s", ex)
            return ""
