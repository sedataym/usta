"""Values crossing OCR/translation application boundaries."""

from dataclasses import dataclass


@dataclass(frozen=True)
class OCRResult:
    text: str
    confidence: float | None = None


@dataclass(frozen=True)
class TranslationRequest:
    text: str
    source_lang: str
    target_lang: str
    engine_name: str
    session_id: int


@dataclass(frozen=True)
class TranslationResult:
    translated_text: str
    source_lang: str
    target_lang: str
    engine_name: str
    session_id: int


class EngineError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message
