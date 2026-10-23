from abc import ABC, abstractmethod


class BaseOCREngine(ABC):
    @abstractmethod
    def read_text(self, image_path: str) -> str:
        """Reads text from image and returns cleaned text."""
        pass

    @abstractmethod
    def set_language(self, lang_code: str):
        """Sets the language for OCR."""
        pass
