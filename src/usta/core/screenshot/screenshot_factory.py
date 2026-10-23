import logging
import platform

from usta.core.screenshot.base_screenshot import BaseScreenshot
from usta.core.screenshot.spectacle_screenshot import SpectacleScreenshot

logger = logging.getLogger(__name__)

try:
    from usta.core.screenshot.macos_screenshot import MacOSScreenshot
except Exception as exc:
    MacOSScreenshot = None
    _MACOS_IMPORT_ERROR = exc
else:
    _MACOS_IMPORT_ERROR = None

try:
    from usta.core.screenshot.portal_screenshot import PortalScreenshot
except Exception as exc:
    PortalScreenshot = None
    _PORTAL_IMPORT_ERROR = exc
else:
    _PORTAL_IMPORT_ERROR = None
 
class ScreenshotFactory:
    @staticmethod
    def get_engine(engine_name: str = "Portal") -> BaseScreenshot:
        if platform.system() == "Darwin":
            if MacOSScreenshot is not None and MacOSScreenshot.is_available():
                return MacOSScreenshot()

            if _MACOS_IMPORT_ERROR is not None:
                logger.error(f"macOS ekran görüntüsü motoru kullanılamıyor: {_MACOS_IMPORT_ERROR}")

        if engine_name == "Portal":
            if PortalScreenshot is not None and PortalScreenshot.is_available():
                return PortalScreenshot()

            if _PORTAL_IMPORT_ERROR is not None:
                logger.error(f"Portal screenshot engine unavailable: {_PORTAL_IMPORT_ERROR}")
            logger.info("Falling back to Spectacle screenshot engine.")
            return SpectacleScreenshot()

        # Spectacle
        return SpectacleScreenshot()
