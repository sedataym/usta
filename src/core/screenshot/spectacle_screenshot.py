import os
import subprocess
from PIL import Image
from PySide6.QtCore import QRect
from src.core.screenshot.base_screenshot import BaseScreenshot
from src.config import FULL_SCREEN_TEMP_PATH

class SpectacleScreenshot(BaseScreenshot):
    def capture(self, rect: QRect, output_path: str, dpi_scale: float = 1.0) -> bool:
        if os.path.exists(FULL_SCREEN_TEMP_PATH):
            os.remove(FULL_SCREEN_TEMP_PATH)
        
        try:
            # Use spectacle for KDE/Wayland
            subprocess.run(
                ["spectacle", "-b", "-f", "-n", "-o", FULL_SCREEN_TEMP_PATH],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
            )
            
            if not os.path.exists(FULL_SCREEN_TEMP_PATH):
                return False
            
            with Image.open(FULL_SCREEN_TEMP_PATH) as full_img:
                # Apply DPI scaling to convert logical coordinates to physical pixels
                x1 = max(0, int(rect.x() * dpi_scale))
                y1 = max(0, int(rect.y() * dpi_scale))
                x2 = min(full_img.width, int((rect.x() + rect.width()) * dpi_scale))
                y2 = min(full_img.height, int((rect.y() + rect.height()) * dpi_scale))
                crop = full_img.crop((x1, y1, x2, y2))
                crop.save(output_path)
            return True
        except Exception as e:
            print(f"Spectacle Capture Error: {e}")
            return False
