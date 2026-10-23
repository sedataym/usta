import logging
import os
import subprocess

from PIL import Image
from PySide6.QtCore import QRect

from usta.config import FULL_SCREEN_TEMP_PATH
from usta.core.screenshot.base_screenshot import BaseScreenshot

logger = logging.getLogger(__name__)


class SpectacleScreenshot(BaseScreenshot):
    def __init__(self, full_screen_path=FULL_SCREEN_TEMP_PATH):
        self.full_screen_path = full_screen_path

    def capture(self, rect: QRect, output_path: str, dpi_scale: float = 1.0) -> bool:
        if os.path.exists(self.full_screen_path):
            os.remove(self.full_screen_path)

        try:
            # Use spectacle for KDE/Wayland
            subprocess.run(
                ["spectacle", "-b", "-f", "-n", "-o", self.full_screen_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
                timeout=15,
            )

            if not os.path.exists(self.full_screen_path):
                return False

            with Image.open(self.full_screen_path) as full_img:
                # Apply DPI scaling to convert logical coordinates to physical pixels
                x1 = max(0, int(rect.x() * dpi_scale))
                y1 = max(0, int(rect.y() * dpi_scale))
                x2 = min(full_img.width, int((rect.x() + rect.width()) * dpi_scale))
                y2 = min(full_img.height, int((rect.y() + rect.height()) * dpi_scale))
                crop = full_img.crop((x1, y1, x2, y2))
                crop.save(output_path)
            return True
        except Exception as e:
            logger.error(f"Spectacle Capture Error: {e}")
            return False
