from src.core.screenshot.base_screenshot import BaseScreenshot
from src.core.screenshot.spectacle_screenshot import SpectacleScreenshot

try:
    from src.core.screenshot.portal_screenshot import PortalScreenshot
except Exception as exc:
    PortalScreenshot = None
    _PORTAL_IMPORT_ERROR = exc
else:
    _PORTAL_IMPORT_ERROR = None
 
class ScreenshotFactory:
    @staticmethod
    def portal_unavailable_reason() -> str | None:
        if _PORTAL_IMPORT_ERROR is not None:
            return str(_PORTAL_IMPORT_ERROR)
        if PortalScreenshot is not None and hasattr(PortalScreenshot, "availability_error"):
            return PortalScreenshot.availability_error()
        return "Portal screenshot engine is unavailable."

    @staticmethod
    def get_engine(engine_name: str = "Portal") -> BaseScreenshot:
        if engine_name == "Portal":
            if PortalScreenshot is not None and PortalScreenshot.is_available():
                return PortalScreenshot()

            portal_error = ScreenshotFactory.portal_unavailable_reason()
            print(f"Portal screenshot engine unavailable: {portal_error}")
            raise RuntimeError(portal_error)

        # Spectacle
        return SpectacleScreenshot()
