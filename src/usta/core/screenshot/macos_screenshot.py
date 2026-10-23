import sys

from PIL import ImageGrab
from PySide6.QtCore import QRect

from usta.core.screenshot.base_screenshot import BaseScreenshot


class MacOSScreenshot(BaseScreenshot):
    @staticmethod
    def is_available() -> bool:
        return sys.platform == "darwin"

    def capture(self, rect: QRect, output_path: str, dpi_scale: float = 1.0) -> bool:
        try:
            full_img = ImageGrab.grab(all_screens=True)

            x1 = max(0, int(rect.x() * dpi_scale))
            y1 = max(0, int(rect.y() * dpi_scale))
            x2 = min(full_img.width, int((rect.x() + rect.width()) * dpi_scale))
            y2 = min(full_img.height, int((rect.y() + rect.height()) * dpi_scale))

            if x2 <= x1 or y2 <= y1:
                return False

            crop = full_img.crop((x1, y1, x2, y2))
            if crop.mode != "RGB":
                crop = crop.convert("RGB")

            crop.save(output_path)
            return True
        except Exception as e:
            print(f"macOS ekran görüntüsü alınamadı: {e}")
            return False
