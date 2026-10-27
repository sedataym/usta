"""Capture inside USTA's process so screen access belongs to the application."""

import io
import math
import sys
import threading

from PIL import Image
from PySide6.QtCore import QRect

from usta.core.exceptions import ScreenCaptureError, ScreenCapturePermissionError
from usta.core.screenshot.base_screenshot import BaseScreenshot

_PERMISSION_MESSAGE = (
    "Screen Recording access is unavailable. Enable USTA in System Settings > "
    "Privacy & Security > Screen & System Audio Recording, then quit and reopen USTA."
)


class MacOSScreenshot(BaseScreenshot):
    CAPTURE_TIMEOUT_SECONDS = 5

    def __init__(self):
        self._permission_requested = False

    @staticmethod
    def is_available() -> bool:
        return sys.platform == "darwin"

    def _capture_region(self, rect):
        import AppKit
        import objc
        import Quartz
        import ScreenCaptureKit

        if not Quartz.CGPreflightScreenCaptureAccess():
            if not self._permission_requested:
                self._permission_requested = True
                Quartz.CGRequestScreenCaptureAccess()
            if not Quartz.CGPreflightScreenCaptureAccess():
                raise ScreenCapturePermissionError(_PERMISSION_MESSAGE)

        done = threading.Event()
        result = {}

        def completed(image, error):
            try:
                if error is not None:
                    if error.code() == ScreenCaptureKit.SCStreamErrorUserDeclined:
                        raise ScreenCapturePermissionError(_PERMISSION_MESSAGE)
                    raise ScreenCaptureError(str(error.localizedDescription()))
                if image is None:
                    raise ScreenCaptureError("macOS returned no screen image.")
                with objc.autorelease_pool():
                    bitmap = AppKit.NSBitmapImageRep.alloc().initWithCGImage_(image)
                    png = bitmap.representationUsingType_properties_(
                        AppKit.NSBitmapImageFileTypePNG, {}
                    )
                    if png is None:
                        raise ScreenCaptureError("macOS could not encode the captured image.")
                    with Image.open(io.BytesIO(bytes(png))) as frame:
                        result["image"] = frame.convert("RGB")
            except Exception as exc:
                result["error"] = exc
            finally:
                done.set()

        manager = ScreenCaptureKit.SCScreenshotManager
        if not hasattr(manager, "captureImageInRect_completionHandler_"):
            raise ScreenCaptureError("Native region capture requires macOS 15.2 or newer.")
        manager.captureImageInRect_completionHandler_(
            Quartz.CGRectMake(rect.x(), rect.y(), rect.width(), rect.height()), completed
        )
        if not done.wait(self.CAPTURE_TIMEOUT_SECONDS):
            raise ScreenCaptureError("macOS screen capture timed out; stop and try again.")
        if "error" in result:
            raise result["error"]
        return result["image"]

    def capture(self, rect: QRect, output_path: str, dpi_scale: float = 1.0) -> bool:
        if (
            rect.width() <= 0
            or rect.height() <= 0
            or not math.isfinite(dpi_scale)
            or dpi_scale <= 0
        ):
            return False
        try:
            frame = self._capture_region(rect)
            size = (
                max(1, round(rect.width() * dpi_scale)),
                max(1, round(rect.height() * dpi_scale)),
            )
            if frame.size != size:
                frame = frame.resize(size, Image.Resampling.LANCZOS)
            frame.save(output_path)
            return True
        except ScreenCaptureError:
            raise
        except Exception as exc:
            raise ScreenCaptureError(f"macOS screen capture failed: {exc}") from exc
