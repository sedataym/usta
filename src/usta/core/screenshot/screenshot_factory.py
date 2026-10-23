"""Load only the selected platform's native screenshot implementation."""
import logging
import platform
from usta.config import FULL_SCREEN_TEMP_PATH
from usta.core.screenshot.base_screenshot import BaseScreenshot

logger = logging.getLogger(__name__)

class ScreenshotFactory:
    @staticmethod
    def get_engine(engine_name: str = 'Portal', full_screen_path=FULL_SCREEN_TEMP_PATH) -> BaseScreenshot:
        if platform.system() == 'Darwin':
            from usta.core.screenshot.macos_screenshot import MacOSScreenshot
            if MacOSScreenshot.is_available():
                return MacOSScreenshot()
        if engine_name == 'Portal':
            from usta.core.screenshot.portal_screenshot import PortalScreenshot
            if PortalScreenshot.is_available():
                return PortalScreenshot(full_screen_path)
            logger.warning('Portal screenshot engine unavailable; falling back to Spectacle')
        from usta.core.screenshot.spectacle_screenshot import SpectacleScreenshot
        return SpectacleScreenshot(full_screen_path)
