import asyncio
from googletrans import Translator
from src.config import get_translation_language_code
from src.core.translation.base_translator import BaseTranslator


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
            print(f"Google Translation Error: {e}")
            return f"Error: {e}"
