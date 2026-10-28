from abc import ABC, abstractmethod


class BaseTranslator(ABC):
    @abstractmethod
    def translate(self, text: str) -> str:
        """Translates text to target language."""
        pass

    @abstractmethod
    def set_languages(self, source: str, target: str):
        """Updates source and target languages."""
        pass
