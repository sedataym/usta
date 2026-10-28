"""Screenshot interfaces; native engines are loaded only when selected."""

from usta.core.screenshot.base_screenshot import BaseScreenshot
from usta.core.screenshot.image_processor import ImageProcessor
from usta.core.screenshot.screenshot_factory import ScreenshotFactory

__all__ = ["BaseScreenshot", "ImageProcessor", "ScreenshotFactory"]
