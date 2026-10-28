"""Opt-in real ScreenCaptureKit check; never opens a permission request."""

import importlib.util
import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QWidget


@unittest.skipUnless(
    sys.platform == "darwin"
    and os.environ.get("USTA_NATIVE_TESTS") == "1"
    and importlib.util.find_spec("ScreenCaptureKit") is not None,
    "Requires native macOS and ScreenCaptureKit",
)
class NativeMacOSCaptureTests(unittest.TestCase):
    def test_worker_captures_test_window_without_external_process_or_permission_request(self):
        import Quartz

        from usta.core.screenshot.macos_screenshot import MacOSScreenshot

        if not Quartz.CGPreflightScreenCaptureAccess():
            self.skipTest("Test runner lacks Screen Recording access; permission was not requested")
        app = QApplication.instance() or QApplication([])
        window = QWidget()
        window.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        window.setStyleSheet("background: white;")
        window.setGeometry(100, 100, 160, 80)
        window.show()
        window.raise_()
        QTest.qWait(300)
        region = window.frameGeometry()
        outcome = {}
        with tempfile.TemporaryDirectory(prefix="usta-native-capture-") as directory:
            output = Path(directory) / "frame.png"

            def capture():
                try:
                    outcome["ok"] = MacOSScreenshot().capture(region, str(output), 2)
                except Exception as exc:
                    outcome["error"] = exc

            with (
                patch.object(
                    Quartz, "CGRequestScreenCaptureAccess", side_effect=AssertionError("request")
                ),
                patch("PIL.ImageGrab.grab", side_effect=AssertionError("external capture")),
            ):
                worker = threading.Thread(target=capture)
                worker.start()
                deadline = time.monotonic() + 7
                while worker.is_alive() and time.monotonic() < deadline:
                    QTest.qWait(10)
                worker.join(timeout=0.1)
            window.close()
            app.processEvents()
            self.assertFalse(worker.is_alive(), "ScreenCaptureKit did not finish")
            self.assertNotIn("error", outcome, outcome.get("error"))
            self.assertTrue(outcome.get("ok"))
            with Image.open(output) as image:
                self.assertEqual(image.size, (region.width() * 2, region.height() * 2))
                self.assertTrue(
                    all(
                        channel > 240
                        for channel in image.getpixel((image.width // 2, image.height // 2))
                    ),
                    f"region={region}, center={image.getpixel((image.width // 2, image.height // 2))}",
                )
