from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class TranslationResult:
    translated_text: str
    source_lang: str = "en"
    target_lang: str = "tr"
    engine_name: str = "unknown"

class BaseTranslator(ABC):
    @abstractmethod
    def translate(self, text: str) -> str:
        """Translates text to target language."""
        pass

    @abstractmethod
    def set_languages(self, source: str, target: str):
        """Updates source and target languages."""
        pass
