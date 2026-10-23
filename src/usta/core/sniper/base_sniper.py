from abc import ABC, abstractmethod
from PySide6.QtCore import QRect

class BaseSniper(ABC):
    @abstractmethod
    def get_region(self) -> QRect | None:
        """Selects a region on the screen and returns its coordinates."""
        pass
