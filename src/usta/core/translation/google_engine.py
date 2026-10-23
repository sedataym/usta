import logging
import asyncio
from usta.application.results import EngineError
from googletrans import Translator
from usta.config import get_translation_language_code
from usta.core.translation.base_translator import BaseTranslator

logger = logging.getLogger(__name__)


class GoogleEngine(BaseTranslator):
    def __init__(self, source='en', target='tr'):
        self.source = source
        self.target = target

    def set_languages(self, source: str, target: str):
        self.source = source
        self.target = target

    def translate(self, text: str) -> str:
        try:
            source = get_translation_language_code(self.source, "google", "source")
            target = get_translation_language_code(self.target, "google", "target")

            async def translate_text():
                async with Translator(timeout=10) as translator:
                    result = await translator.translate(text, src=source, dest=target)
                    return result.text

            return asyncio.run(translate_text())
        except Exception as e:
            raise EngineError("translation", "Google translation failed; check the connection.") from e
