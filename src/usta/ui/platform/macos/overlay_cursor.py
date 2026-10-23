"""Cursor tracking for nonactivating overlays, including while NSApp is inactive.

Qt/Cocoa skips mouseMovedImpl/cursorUpdate for an inactive application. An
always-active native tracking area updates only this overlay's cursor and never
activates the application or monitors events from other applications.
"""

import weakref

import AppKit
import objc
from PySide6.QtCore import QBuffer, QIODevice, QObject, QPoint, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap


def _remove_tracking_area(state):
    view, area = state["view"], state["area"]
    if view is not None and area is not None:
        view.removeTrackingArea_(area)
    state.update(view=None, area=None, owner=None)
    _restore_cursor(state)


def _restore_cursor(state):
    previous, applied = state["previous_cursor"], state["applied_cursor"]
    if previous is not None and AppKit.NSCursor.currentCursor() == applied:
        previous.set()
    state.update(previous_cursor=None, applied_cursor=None)


class _USTAOverlayTrackingOwner(AppKit.NSObject):
    def mouseEntered_(self, event):
        if controller := self.reference():
            controller.mouse_moved(event)

    def mouseMoved_(self, event):
        if controller := self.reference():
            controller.mouse_moved(event)

    def mouseExited_(self, event):
        if controller := self.reference():
            controller.mouse_exited()


def _diagonal_cursor(shape):
    """Public-API fallback for macOS versions predating frame-resize cursors."""
    pixmap = QPixmap(48, 48)
    pixmap.setDevicePixelRatio(2)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.translate(12, 12)
    painter.rotate(45 if shape == Qt.SizeFDiagCursor else -45)
    path = QPainterPath()
    path.moveTo(-8, 0)
    path.lineTo(8, 0)
    for x, inward in ((-8, 1), (8, -1)):
        path.moveTo(x + inward * 4, -4)
        path.lineTo(x, 0)
        path.lineTo(x + inward * 4, 4)
    for color, width in (("white", 4.5), ("black", 2.0)):
        painter.strokePath(
            path, QPen(QColor(color), width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        )
    painter.end()
    buffer = QBuffer()
    buffer.open(QIODevice.WriteOnly)
    pixmap.save(buffer, "PNG")
    image = AppKit.NSImage.alloc().initWithData_(bytes(buffer.data()))
    image.setSize_((24, 24))
    return AppKit.NSCursor.alloc().initWithImage_hotSpot_(image, (12, 12))


class MacOSOverlayCursor(QObject):
    def __init__(self, widget):
        super().__init__(widget)
        self._widget = weakref.ref(widget)
        self._hovering = False
        self._cursors = {}
        self._state = dict(
            view=None, area=None, owner=None, previous_cursor=None, applied_cursor=None
        )
        state = self._state
        self.destroyed.connect(lambda: _remove_tracking_area(state))

    def start(self):
        widget = self._widget()
        view = objc.objc_object(c_void_p=int(widget.winId()))
        if self._state["view"] == view:
            return
        self.stop()
        owner = _USTAOverlayTrackingOwner.alloc().init()
        owner.reference = weakref.ref(self)
        options = (
            AppKit.NSTrackingMouseEnteredAndExited
            | AppKit.NSTrackingMouseMoved
            | AppKit.NSTrackingActiveAlways
            | AppKit.NSTrackingInVisibleRect
            | AppKit.NSTrackingEnabledDuringMouseDrag
        )
        area = AppKit.NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(
            view.bounds(), options, owner, None
        )
        self._state.update(view=view, area=area, owner=owner)
        view.addTrackingArea_(area)

    def stop(self):
        self._hovering = False
        _remove_tracking_area(self._state)

    def mouse_moved(self, event):
        widget, view = self._widget(), self._state["view"]
        if widget is None or view is None or not widget.isVisible():
            return
        window = view.window()
        if window is None:
            return
        if widget._drag_mode is None:
            screen_point = window.convertPointToScreen_(event.locationInWindow())
            top_window = AppKit.NSWindow.windowNumberAtPoint_belowWindowWithWindowNumber_(
                screen_point, 0
            )
            if top_window != window.windowNumber():
                self.mouse_exited()
                return
        point = view.convertPoint_fromView_(event.locationInWindow(), None)
        position = QPoint(
            round(point.x), round(point.y if view.isFlipped() else widget.height() - point.y)
        )
        if not widget.rect().contains(position):
            self.mouse_exited()
            return
        self._hovering = True
        widget._set_hovered(True)
        if widget._drag_mode is None:
            widget._update_hover_cursor(position)
        else:
            self.apply_cursor(widget.cursor().shape())

    def mouse_exited(self):
        widget = self._widget()
        if widget is not None and widget._drag_mode is not None:
            return  # Keep the drag cursor until release, even outside the window.
        self._hovering = False
        if widget is not None:
            widget._set_hovered(False)
            widget.unsetCursor()
            widget.label.unsetCursor()
        _restore_cursor(self._state)

    def apply_cursor(self, shape):
        if shape == Qt.ArrowCursor:
            self.mouse_exited()
            return
        widget = self._widget()
        if widget is None or (not self._hovering and widget._drag_mode is None):
            return
        if self._state["previous_cursor"] is None:
            self._state["previous_cursor"] = AppKit.NSCursor.currentCursor()
        dragging = widget._drag_mode == "move"
        key = (shape, dragging)
        if key not in self._cursors:
            self._cursors[key] = self._make_cursor(shape, dragging)
        cursor = self._cursors[key]
        cursor.set()  # QWidget.setCursor alone is ignored while NSApp is inactive.
        self._state["applied_cursor"] = cursor

    @staticmethod
    def _make_cursor(shape, dragging):
        if shape == Qt.SizeAllCursor:
            return (
                AppKit.NSCursor.closedHandCursor() if dragging else AppKit.NSCursor.openHandCursor()
            )
        if shape == Qt.SizeHorCursor:
            return AppKit.NSCursor.resizeLeftRightCursor()
        if shape == Qt.SizeVerCursor:
            return AppKit.NSCursor.resizeUpDownCursor()
        if shape in (Qt.SizeFDiagCursor, Qt.SizeBDiagCursor):
            if hasattr(AppKit.NSCursor, "frameResizeCursorFromPosition_inDirections_"):
                position = (
                    AppKit.NSCursorFrameResizePositionTopLeft
                    if shape == Qt.SizeFDiagCursor
                    else AppKit.NSCursorFrameResizePositionTopRight
                )
                return AppKit.NSCursor.frameResizeCursorFromPosition_inDirections_(
                    position, AppKit.NSCursorFrameResizeDirectionsAll
                )
            return _diagonal_cursor(shape)
        return AppKit.NSCursor.arrowCursor()
