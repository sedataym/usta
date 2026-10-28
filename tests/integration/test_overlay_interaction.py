"""Hover feedback matches actual overlay move/resize operations."""

import unittest
from unittest.mock import patch

from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication

from usta.ui.overlay_window import TransparentOverlay


class OverlayInteractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.os_patch = patch("usta.ui.overlay_window.OS", "Linux")
        self.hotkey_patch = patch("usta.core.shortcut.GlobalHotkey.start", return_value=False)
        self.os_patch.start()
        self.hotkey_patch.start()
        self.addCleanup(self.os_patch.stop)
        self.addCleanup(self.hotkey_patch.stop)
        self.overlay = TransparentOverlay()
        self.overlay.setGeometry(100, 100, 400, 200)
        self.overlay.show()
        self.app.processEvents()
        self.addCleanup(self.overlay.close)

    def mouse(self, kind, local, *, global_pos=None, buttons=Qt.NoButton):
        position = QPoint(*local)
        global_pos = global_pos or self.overlay.mapToGlobal(position)
        button = (
            Qt.LeftButton
            if kind in (QEvent.MouseButtonPress, QEvent.MouseButtonRelease)
            else Qt.NoButton
        )
        event = QMouseEvent(
            kind, QPointF(position), QPointF(global_pos), button, buttons, Qt.NoModifier
        )
        self.app.sendEvent(self.overlay, event)

    def test_all_edges_and_corners_show_the_matching_cursor_in_both_modes(self):
        cases = [
            ((2, 100), Qt.SizeHorCursor),
            ((398, 100), Qt.SizeHorCursor),
            ((200, 2), Qt.SizeVerCursor),
            ((200, 198), Qt.SizeVerCursor),
            ((2, 2), Qt.SizeFDiagCursor),
            ((398, 198), Qt.SizeFDiagCursor),
            ((398, 2), Qt.SizeBDiagCursor),
            ((2, 198), Qt.SizeBDiagCursor),
            ((200, 100), Qt.SizeAllCursor),
        ]
        for scan in (False, True):
            self.overlay.set_mode(scan)
            for position, expected in cases:
                with self.subTest(scan=scan, position=position):
                    self.mouse(QEvent.MouseMove, position)
                    self.assertEqual(self.overlay.cursor().shape(), expected)
                    self.assertEqual(self.overlay.label.cursor().shape(), expected)

    def test_left_top_resize_preserves_opposite_corner(self):
        before = self.overlay.geometry()
        local = (2, 2)
        origin = self.overlay.mapToGlobal(QPoint(*local))
        self.mouse(QEvent.MouseButtonPress, local, buttons=Qt.LeftButton)
        self.mouse(
            QEvent.MouseMove, local, global_pos=origin + QPoint(-40, -30), buttons=Qt.LeftButton
        )
        after = self.overlay.geometry()
        self.assertEqual(after.bottomRight(), before.bottomRight())
        self.assertEqual(after.width(), before.width() + 40)
        self.assertEqual(after.height(), before.height() + 30)
        self.assertEqual(self.overlay.cursor().shape(), Qt.SizeFDiagCursor)

    def test_left_resize_respects_minimum_width_and_keeps_right_edge(self):
        before = self.overlay.geometry()
        origin = self.overlay.mapToGlobal(QPoint(2, 100))
        self.mouse(QEvent.MouseButtonPress, (2, 100), buttons=Qt.LeftButton)
        self.mouse(
            QEvent.MouseMove, (2, 100), global_pos=origin + QPoint(1000, 0), buttons=Qt.LeftButton
        )
        self.assertEqual(self.overlay.width(), 200)
        self.assertEqual(self.overlay.geometry().right(), before.right())

    def test_center_drag_moves_without_resizing_and_release_refreshes_cursor(self):
        before = self.overlay.geometry()
        origin = self.overlay.mapToGlobal(QPoint(200, 100))
        self.mouse(QEvent.MouseButtonPress, (200, 100), buttons=Qt.LeftButton)
        self.mouse(
            QEvent.MouseMove, (200, 100), global_pos=origin + QPoint(30, 20), buttons=Qt.LeftButton
        )
        self.assertEqual(self.overlay.geometry().size(), before.size())
        self.assertEqual(self.overlay.pos(), before.topLeft() + QPoint(30, 20))
        self.mouse(QEvent.MouseButtonRelease, (2, 100))
        self.assertEqual(self.overlay.cursor().shape(), Qt.SizeHorCursor)

    def test_entering_edge_refreshes_cursor_without_an_extra_move(self):
        self.overlay.set_mode(True)
        edge = self.overlay.mapToGlobal(QPoint(2, 100))
        with patch("usta.ui.overlay_window.QCursor.pos", return_value=edge):
            self.app.sendEvent(self.overlay, QEvent(QEvent.Enter))
        self.assertEqual(self.overlay.cursor().shape(), Qt.SizeHorCursor)

    def test_bottom_right_resize_preserves_existing_behavior_and_minimum_height(self):
        before = self.overlay.geometry()
        origin = self.overlay.mapToGlobal(QPoint(398, 198))
        self.mouse(QEvent.MouseButtonPress, (398, 198), buttons=Qt.LeftButton)
        self.mouse(
            QEvent.MouseMove, (398, 198), global_pos=origin + QPoint(50, 20), buttons=Qt.LeftButton
        )
        self.assertEqual(self.overlay.geometry().topLeft(), before.topLeft())
        self.assertEqual(self.overlay.width(), before.width() + 50)
        self.assertEqual(self.overlay.height(), before.height() + 20)
        self.mouse(
            QEvent.MouseMove,
            (398, 198),
            global_pos=origin + QPoint(-1000, -1000),
            buttons=Qt.LeftButton,
        )
        self.assertEqual(self.overlay.width(), 200)
        self.assertEqual(self.overlay.height(), 60)

    def test_leaving_overlay_clears_hover_cursor(self):
        self.mouse(QEvent.MouseMove, (2, 100))
        self.assertEqual(self.overlay.cursor().shape(), Qt.SizeHorCursor)
        self.app.sendEvent(self.overlay, QEvent(QEvent.Leave))
        self.assertEqual(self.overlay.cursor().shape(), Qt.ArrowCursor)
        self.assertEqual(self.overlay.label.cursor().shape(), Qt.ArrowCursor)
