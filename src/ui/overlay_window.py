from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from src.config import SETTINGS_TOPMOST_HOTKEY
from src.core.shortcut import GlobalHotkey
from src.i18n import _

class CornerLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.corner_line_length = 24
        self.corner_line_thickness = 2
        self._show_corner_lines = False

    def set_corner_lines_visible(self, visible):
        if self._show_corner_lines == visible:
            return
        self._show_corner_lines = visible
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self._show_corner_lines:
            return

        parent = self.parent()
        color = QColor(parent.font_color if parent is not None else "white")
        if not color.isValid():
            color = QColor("white")

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(color, self.corner_line_thickness, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))

        offset = self.corner_line_thickness / 2
        left = offset
        top = offset
        right = self.width() - 1 - offset
        bottom = self.height() - 1 - offset
        length = self.corner_line_length
        radius = min(8, length / 3)

        paths = []

        top_left = QPainterPath()
        top_left.moveTo(left + length, top)
        top_left.lineTo(left + radius, top)
        top_left.quadTo(left, top, left, top + radius)
        top_left.lineTo(left, top + length)
        paths.append(top_left)

        top_right = QPainterPath()
        top_right.moveTo(right - length, top)
        top_right.lineTo(right - radius, top)
        top_right.quadTo(right, top, right, top + radius)
        top_right.lineTo(right, top + length)
        paths.append(top_right)

        bottom_left = QPainterPath()
        bottom_left.moveTo(left, bottom - length)
        bottom_left.lineTo(left, bottom - radius)
        bottom_left.quadTo(left, bottom, left + radius, bottom)
        bottom_left.lineTo(left + length, bottom)
        paths.append(bottom_left)

        bottom_right = QPainterPath()
        bottom_right.moveTo(right - length, bottom)
        bottom_right.lineTo(right - radius, bottom)
        bottom_right.quadTo(right, bottom, right, bottom - radius)
        bottom_right.lineTo(right, bottom - length)
        paths.append(bottom_right)

        for path in paths:
            painter.drawPath(path)


class TransparentOverlay(QWidget):
    main_window_topmost_requested = Signal(bool)
    settings_topmost_hotkey_pressed = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("USTA_TRANSLATION_OVERLAY")
        self.setWindowFlags(Qt.WindowStaysOnTopHint |
                            Qt.FramelessWindowHint |
                            Qt.WindowDoesNotAcceptFocus |
                            Qt.Tool |
                            Qt.X11BypassWindowManagerHint)

        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setMouseTracking(True)
        self.resize(800, 200)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Style variables
        self.font_family = "Arial"
        self.font_size = 20
        self.font_color = "white"
        self.bg_color = "#000000"
        self.bg_opacity = 180
        self._show_corner_lines = False
        
        self.label = CornerLabel(self)
        self.label.setText("Translation will appear here.")
        self.label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignCenter)
        self.update_style()
        self.layout.addWidget(self.label)

        self._main_window_topmost_requested = False
        self._settings_topmost_hotkey_armed = True
        self._settings_topmost_hotkey = GlobalHotkey(
            SETTINGS_TOPMOST_HOTKEY,
            self._emit_settings_topmost_hotkey_pressed,
        )
        self.settings_topmost_hotkey_pressed.connect(self._handle_settings_topmost_hotkey_pressed)
        self._settings_topmost_hotkey.start()
        
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(lambda: self.label.setText(""))

        self.set_mode(False)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.raise_)
        self.timer.start(2000)

        # Manual drag state (X11BypassWindowManagerHint bypasses WM)
        self._drag_mode = None  # "move" or "resize"
        self._drag_start_pos = None
        self._drag_start_geometry = None

    def _emit_settings_topmost_hotkey_pressed(self):
        self.settings_topmost_hotkey_pressed.emit()

    @Slot()
    def _handle_settings_topmost_hotkey_pressed(self):
        if not self._settings_topmost_hotkey_armed:
            return

        self._settings_topmost_hotkey_armed = False
        self._toggle_main_window_topmost()
        QTimer.singleShot(200, self._rearm_settings_topmost_hotkey)

    def _rearm_settings_topmost_hotkey(self):
        self._settings_topmost_hotkey_armed = True

    def update_style(self):
        r = int(self.bg_color[1:3], 16)
        g = int(self.bg_color[3:5], 16)
        b = int(self.bg_color[5:7], 16)
        style = (
            f"color: {self.font_color}; "
            f"font-family: '{self.font_family}'; "
            f"font-size: {self.font_size}px; "
            f"font-weight: bold; "
            f"background: rgba({r},{g},{b},{self.bg_opacity}); border-radius: 6px; padding: 10px;"
        )
        self.label.setStyleSheet(style)
        self.label.update()

    def enterEvent(self, event):
        self._show_corner_lines = True
        self.label.set_corner_lines_visible(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._show_corner_lines = False
        self.label.set_corner_lines_visible(False)
        super().leaveEvent(event)

    @Slot(str)
    def set_font_family(self, family):
        self.font_family = family
        self.update_style()

    @Slot(int)
    def set_font_size(self, size):
        self.font_size = size
        self.update_style()

    @Slot(str)
    def set_font_color(self, color):
        self.font_color = color
        self.update_style()

    @Slot(str)
    def set_bg_color(self, color):
        self.bg_color = color
        self.update_style()

    @Slot(int)
    def set_bg_opacity(self, opacity):
        self.bg_opacity = opacity
        self.update_style()

    @Slot(str)
    def update_text(self, text):
        self.label.setText(text)
        self.raise_()
        self.hide_timer.start(10000)

    def _toggle_main_window_topmost(self):
        self._main_window_topmost_requested = not self._main_window_topmost_requested
        self.main_window_topmost_requested.emit(self._main_window_topmost_requested)

    def closeEvent(self, event):
        self._settings_topmost_hotkey.stop()
        super().closeEvent(event)

    def set_mode(self, scan):
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setCursor(Qt.ArrowCursor if scan else Qt.SizeAllCursor)
        if scan:
            self.hide_timer.start(10000)
        else:
            self.hide_timer.stop()
            self.label.setText(_("Translation will appear here."))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start_pos = event.globalPosition().toPoint()
            self._drag_start_geometry = self.geometry()
            if event.position().x() > self.width() - 20 and event.position().y() > self.height() - 20:
                self._drag_mode = "resize"
                self.setCursor(Qt.SizeFDiagCursor)
            else:
                self._drag_mode = "move"
                self.setCursor(Qt.SizeAllCursor)
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_mode is None:
            if event.position().x() > self.width() - 20 and event.position().y() > self.height() - 20:
                self.setCursor(Qt.SizeFDiagCursor)
            else:
                self.setCursor(Qt.SizeAllCursor)
            return

        if self._drag_start_pos is None:
            return

        delta = event.globalPosition().toPoint() - self._drag_start_pos
        if self._drag_mode == "move":
            self.move(self._drag_start_geometry.x() + delta.x(),
                      self._drag_start_geometry.y() + delta.y())
        elif self._drag_mode == "resize":
            new_w = max(200, self._drag_start_geometry.width() + delta.x())
            new_h = max(60, self._drag_start_geometry.height() + delta.y())
            self.resize(new_w, new_h)
        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_mode = None
            self._drag_start_pos = None
            self._drag_start_geometry = None
            if event.position().x() > self.width() - 20 and event.position().y() > self.height() - 20:
                self.setCursor(Qt.SizeFDiagCursor)
            else:
                self.setCursor(Qt.SizeAllCursor)
            event.accept()
