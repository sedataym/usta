import io
import tempfile
import unittest
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PIL import Image
from PySide6.QtCore import QRect

from usta.application.pipeline import Pipeline
from usta.core.exceptions import ScreenCaptureError, ScreenCapturePermissionError
from usta.core.screenshot.macos_screenshot import MacOSScreenshot


class MacOSCaptureTests(unittest.TestCase):
    def native_modules(self, *, allowed=True, error=None):
        data = io.BytesIO()
        Image.new("RGB", (80, 40), "white").save(data, format="PNG")
        bitmap = Mock()
        bitmap.representationUsingType_properties_.return_value = data.getvalue()
        appkit = Mock(NSBitmapImageFileTypePNG=4)
        appkit.NSBitmapImageRep.alloc.return_value.initWithCGImage_.return_value = bitmap
        quartz = SimpleNamespace(
            CGPreflightScreenCaptureAccess=Mock(return_value=allowed),
            CGRequestScreenCaptureAccess=Mock(return_value=False),
            CGRectMake=lambda x, y, width, height: ((x, y), (width, height)),
        )
        manager = Mock()
        manager.captureImageInRect_completionHandler_.side_effect = lambda rect, callback: callback(
            object(), error
        )
        return {
            "Quartz": quartz,
            "ScreenCaptureKit": SimpleNamespace(
                SCScreenshotManager=manager, SCStreamErrorUserDeclined=-3801
            ),
            "AppKit": appkit,
            "objc": SimpleNamespace(autorelease_pool=nullcontext),
        }

    def test_missing_access_requests_once_and_never_starts_capture(self):
        modules = self.native_modules(allowed=False)
        engine = MacOSScreenshot()
        with patch.dict("sys.modules", modules):
            for _ in range(2):
                with self.assertRaises(ScreenCapturePermissionError):
                    engine.capture(QRect(0, 0, 40, 20), "unused")
        modules["Quartz"].CGRequestScreenCaptureAccess.assert_called_once()
        modules[
            "ScreenCaptureKit"
        ].SCScreenshotManager.captureImageInRect_completionHandler_.assert_not_called()

    def test_granted_access_captures_in_process_with_negative_coordinates_and_dpi(self):
        modules = self.native_modules()
        with tempfile.TemporaryDirectory() as directory, patch.dict("sys.modules", modules):
            output = Path(directory) / "capture.jpeg"
            with patch("PIL.ImageGrab.grab", side_effect=AssertionError("external grab used")):
                self.assertTrue(MacOSScreenshot().capture(QRect(-20, 30, 40, 20), str(output), 2))
            with Image.open(output) as image:
                self.assertEqual(image.size, (80, 40))
                self.assertEqual(image.mode, "RGB")
        native_call = modules[
            "ScreenCaptureKit"
        ].SCScreenshotManager.captureImageInRect_completionHandler_
        self.assertEqual(native_call.call_args.args[0], ((-20, 30), (40, 20)))
        modules["Quartz"].CGRequestScreenCaptureAccess.assert_not_called()

    def test_native_permission_denial_is_fatal_even_if_preflight_was_granted(self):
        error = SimpleNamespace(code=lambda: -3801, localizedDescription=lambda: "denied")
        with patch.dict("sys.modules", self.native_modules(error=error)):
            with self.assertRaises(ScreenCapturePermissionError):
                MacOSScreenshot().capture(QRect(0, 0, 40, 20), "unused")

    def test_capture_timeout_stops_without_writing_a_late_frame(self):
        modules = self.native_modules()
        modules[
            "ScreenCaptureKit"
        ].SCScreenshotManager.captureImageInRect_completionHandler_.side_effect = None
        with (
            patch.dict("sys.modules", modules),
            patch("usta.core.screenshot.macos_screenshot.threading.Event.wait", return_value=False),
        ):
            with self.assertRaises(ScreenCaptureError):
                MacOSScreenshot().capture(QRect(0, 0, 40, 20), "unused")

    def test_pipeline_stops_after_one_capture_permission_failure(self):
        capture = Mock()
        capture.capture.side_effect = ScreenCapturePermissionError("Screen Recording unavailable")
        errors = []

        def on_error(message):
            errors.append(message)
            if len(errors) == 2:
                pipeline.stop()  # Bound a broken retry loop so the regression cannot hang.

        pipeline = Pipeline(
            capture_factory=lambda name: capture,
            publisher=Mock(),
            image_path="unused",
            ocr_factory=Mock,
            on_translation=Mock(),
            on_error=on_error,
        )
        self.addCleanup(pipeline.close)
        pipeline.start()
        pipeline.run()
        self.assertEqual(errors, ["Screen Recording unavailable"])
        self.assertEqual(capture.capture.call_count, 1)
        capture.close.assert_called_once()
