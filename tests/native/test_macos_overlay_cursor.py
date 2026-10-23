"""Native hover delivery and NSCursor updates without Qt mouse-move events."""

import os
import sys
import unittest
from unittest.mock import patch

from PySide6.QtCore import QEventLoop, Qt, QTimer
from PySide6.QtWidgets import QApplication

from usta.ui.overlay_window import TransparentOverlay


def pump():
    loop = QEventLoop()
    QTimer.singleShot(30, loop.quit)
    loop.exec()


@unittest.skipUnless(
    os.environ.get("USTA_NATIVE_TESTS") == "1" and sys.platform == "darwin", "Requires native macOS"
)
class NativeOverlayCursorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import AppKit
        import objc

        cls.cocoa, cls.objc = AppKit, objc
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        with patch("usta.core.shortcut.GlobalHotkey.start", return_value=False):
            self.overlay = TransparentOverlay()
        self.overlay.setGeometry(160, 160, 400, 200)
        self.overlay.show()
        pump()
        self.addCleanup(self.overlay.close)

    def native_event(self, x, y):
        view = self.objc.objc_object(c_void_p=int(self.overlay.winId()))
        point = (x, y if view.isFlipped() else self.overlay.height() - y)
        location = view.convertPoint_toView_(point, None)
        return self.cocoa.NSEvent.mouseEventWithType_location_modifierFlags_timestamp_windowNumber_context_eventNumber_clickCount_pressure_(
            self.cocoa.NSEventTypeMouseMoved,
            location,
            0,
            0.0,
            view.window().windowNumber(),
            None,
            0,
            0,
            0.0,
        )

    def test_tracking_is_always_active_and_is_removed_on_hide(self):
        helper = self.overlay._macos_cursor
        area = helper._state["area"]
        self.assertTrue(area.options() & self.cocoa.NSTrackingActiveAlways)
        self.assertTrue(area.options() & self.cocoa.NSTrackingMouseMoved)
        self.assertIn(area, helper._state["view"].trackingAreas())
        self.overlay.hide()
        self.assertIsNone(helper._state["area"])
        self.overlay.show()
        pump()
        self.assertIsNotNone(helper._state["area"])

    def test_native_hover_sets_displayed_cursor_before_press_without_activating_app(self):
        helper = self.overlay._macos_cursor
        # Exercise the native callback directly: Qt omits it when NSApp is inactive.
        # Native cursor/tracking objects remain real; no input-event injection needed.
        active = bool(self.cocoa.NSApp.isActive())
        cases = [
            ((2, 100), Qt.SizeHorCursor, self.cocoa.NSCursor.resizeLeftRightCursor()),
            ((200, 2), Qt.SizeVerCursor, self.cocoa.NSCursor.resizeUpDownCursor()),
            ((200, 100), Qt.SizeAllCursor, self.cocoa.NSCursor.openHandCursor()),
        ]
        for (x, y), shape, native in cases:
            with self.subTest(shape=shape):
                self.cocoa.NSCursor.arrowCursor().set()
                helper._state["owner"].mouseMoved_(self.native_event(x, y))
                self.assertIsNone(self.overlay._drag_mode)
                self.assertEqual(self.overlay.cursor().shape(), shape)
                self.assertEqual(self.cocoa.NSCursor.currentCursor(), native)
                self.assertEqual(bool(self.cocoa.NSApp.isActive()), active)
        helper._state["owner"].mouseExited_(self.native_event(401, 100))
        self.assertEqual(self.overlay.cursor().shape(), Qt.ArrowCursor)
        self.assertFalse(helper._hovering)

    def test_dragging_move_uses_closed_hand_and_stop_restores_previous_cursor(self):
        helper = self.overlay._macos_cursor
        helper._state["owner"].mouseMoved_(self.native_event(200, 100))
        self.overlay._drag_mode = "move"
        helper._state["owner"].mouseMoved_(self.native_event(210, 110))
        self.assertEqual(
            self.cocoa.NSCursor.currentCursor(), self.cocoa.NSCursor.closedHandCursor()
        )
        helper.stop()
        self.assertFalse(helper._hovering)
        self.assertIsNone(helper._state["area"])

    def test_diagonal_cursors_have_a_public_api_fallback_for_older_macos(self):
        from types import SimpleNamespace

        native_cursor = self.cocoa.NSCursor
        helper = self.overlay._macos_cursor
        with patch.object(self.cocoa, "NSCursor", SimpleNamespace(alloc=native_cursor.alloc)):
            for shape in (Qt.SizeFDiagCursor, Qt.SizeBDiagCursor):
                cursor = helper._make_cursor(shape, False)
                self.assertIsNotNone(cursor.image().TIFFRepresentation())
                self.assertEqual(tuple(cursor.image().size()), (24.0, 24.0))

    def test_obscured_overlay_does_not_override_another_windows_cursor(self):
        helper = self.overlay._macos_cursor
        from types import SimpleNamespace

        with patch.object(
            self.cocoa,
            "NSWindow",
            SimpleNamespace(
                windowNumberAtPoint_belowWindowWithWindowNumber_=lambda point, below: -1
            ),
        ):
            self.cocoa.NSCursor.arrowCursor().set()
            helper._state["owner"].mouseMoved_(self.native_event(2, 100))
        self.assertFalse(helper._hovering)
        self.assertEqual(self.cocoa.NSCursor.currentCursor(), self.cocoa.NSCursor.arrowCursor())

    def test_repeated_start_does_not_duplicate_tracking_area(self):
        helper = self.overlay._macos_cursor
        original = helper._state["area"]
        helper.start()
        helper.start()
        self.assertEqual(helper._state["area"], original)
        owned = [
            area
            for area in helper._state["view"].trackingAreas()
            if area.owner() == helper._state["owner"]
        ]
        self.assertEqual(len(owned), 1)

    def test_native_corner_hover_applies_diagonal_cursor_without_press(self):
        helper = self.overlay._macos_cursor
        for position, shape in (
            ((2, 2), Qt.SizeFDiagCursor),
            ((398, 2), Qt.SizeBDiagCursor),
            ((2, 198), Qt.SizeBDiagCursor),
            ((398, 198), Qt.SizeFDiagCursor),
        ):
            with self.subTest(position=position):
                helper._state["owner"].mouseMoved_(self.native_event(*position))
                self.assertIsNone(self.overlay._drag_mode)
                self.assertEqual(self.overlay.cursor().shape(), shape)
                self.assertEqual(
                    self.cocoa.NSCursor.currentCursor(), helper._cursors[(shape, False)]
                )
