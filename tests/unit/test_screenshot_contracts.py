import unittest
from unittest.mock import patch

from PySide6.QtCore import QRect

from usta.core.screenshot.macos_screenshot import MacOSScreenshot
from usta.core.screenshot.portal_screenshot import PortalScreenshot
from usta.core.screenshot.screenshot_factory import ScreenshotFactory


class ScreenshotContracts(unittest.TestCase):
    def test_linux_portal_unavailable_preserves_spectacle_fallback(self):
        from usta.core.screenshot.spectacle_screenshot import SpectacleScreenshot

        with (
            patch("platform.system", return_value="Linux"),
            patch.object(PortalScreenshot, "is_available", return_value=False),
        ):
            self.assertIsInstance(ScreenshotFactory.get_engine("Portal"), SpectacleScreenshot)

    def test_macos_uses_native_capture_regardless_of_saved_linux_engine(self):
        with (
            patch("platform.system", return_value="Darwin"),
            patch.object(MacOSScreenshot, "is_available", return_value=True),
        ):
            self.assertIsInstance(ScreenshotFactory.get_engine("Portal"), MacOSScreenshot)

    def test_portal_cancel_propagates_and_closes_resources(self):
        from usta.core.exceptions import PortalCanceledError

        engine = PortalScreenshot()
        self.addCleanup(engine._loop.close)
        with (
            patch.object(engine, "_ensure_dependencies", side_effect=PortalCanceledError()),
            patch.object(engine, "close") as close,
        ):
            with self.assertRaises(PortalCanceledError):
                engine.capture(QRect(0, 0, 100, 50), "/tmp/not-written")
            close.assert_called_once()
