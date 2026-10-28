import logging
import os

import deepl

from usta.application.results import EngineError
from usta.config import get_translation_language_code
from usta.core.translation.base_translator import BaseTranslator

logger = logging.getLogger(__name__)


class DeepLTranslatorEngine(BaseTranslator):
    def __init__(self, api_key=None, source="en", target="tr"):
        self.api_key = api_key or os.getenv("DEEPL_API_KEY", "")
        self.source = source
        self.target = target
        self._translator = None

    @property
    def translator(self):
        if self._translator is None:
            try:
                self._translator = deepl.Translator(self.api_key)
            except Exception as e:
                raise EngineError("initialization", "DeepL could not be initialized") from e
        return self._translator

    def set_api_key(self, api_key: str):
        self.api_key = api_key
        self._translator = None  # reset so next access reinitializes with new key

    def set_languages(self, source: str, target: str):
        self.source = source
        self.target = target

    def translate(self, text: str) -> str:
        if not self.api_key or self.api_key == "YOUR_DEEPL_API_KEY":
            raise EngineError(
                "missing_key", "DeepL API key is missing. Please define DEEPL_API_KEY."
            )

        try:
            if self.translator:
                source_lang = get_translation_language_code(self.source, "deepl", "source")
                target_lang = get_translation_language_code(self.target, "deepl", "target")
                translate_kwargs = {"target_lang": target_lang or self.target}
                if source_lang is not None:
                    translate_kwargs["source_lang"] = source_lang

                result = self.translator.translate_text(text, **translate_kwargs)
                return result.text
            raise EngineError("initialization", "DeepL could not be initialized.")
        except Exception as e:
            raise EngineError(
                "translation", "DeepL translation failed; check credentials and connection."
            ) from e
