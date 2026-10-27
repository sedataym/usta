from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QCursor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from usta.config import OS, SETTINGS_TOPMOST_HOTKEY
from usta.core.shortcut import GlobalHotkey
from usta.i18n import _


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
        painter.setPen(
            QPen(color, self.corner_line_thickness, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        )

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
    RESIZE_MARGIN = 20
    MINIMUM_RESIZE_WIDTH = 200
    MINIMUM_RESIZE_HEIGHT = 60

    main_window_visibility_toggle_requested = Signal()
    settings_topmost_hotkey_pressed = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("USTA_TRANSLATION_OVERLAY")
        window_flags = (
            Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus | Qt.Tool
        )
        if OS == "Linux":
            window_flags |= Qt.X11BypassWindowManagerHint
        self.setWindowFlags(window_flags)

        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self._macos_rules = None
        self._macos_cursor = None
        if OS == "Darwin":
            from usta.ui.platform.macos.overlay import MacOSOverlayRules
            from usta.ui.platform.macos.overlay_cursor import MacOSOverlayCursor

            self.setAttribute(Qt.WA_MacAlwaysShowToolWindow, True)
            self._macos_rules = MacOSOverlayRules(self)
            self._macos_cursor = MacOSOverlayCursor(self)
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
        self.label.setText(_("Translation will appear here."))
        self.label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignCenter)
        self.update_style()
        self.layout.addWidget(self.label)

        self._settings_topmost_hotkey_armed = True
        self.settings_topmost_hotkey = SETTINGS_TOPMOST_HOTKEY
        self._settings_topmost_hotkey = GlobalHotkey(
            self.settings_topmost_hotkey,
            self._emit_settings_topmost_hotkey_pressed,
        )
        self.settings_topmost_hotkey_pressed.connect(self._handle_settings_topmost_hotkey_pressed)
        self._settings_topmost_hotkey.start()

        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(lambda: self.label.setText(""))

        # Manual drag state (X11BypassWindowManagerHint bypasses WM).
        self._drag_mode = None
        self._drag_edges = Qt.Edges()
        self._drag_start_pos = None
        self._drag_start_geometry = None
        self.set_mode(False)

    def showEvent(self, event):
        super().showEvent(event)
        if self._macos_rules is not None:
            self._macos_rules.start()
        if self._macos_cursor is not None:
            self._macos_cursor.start()

    def hideEvent(self, event):
        if self._macos_rules is not None:
            self._macos_rules.stop()
        if self._macos_cursor is not None:
            self._macos_cursor.stop()
        super().hideEvent(event)

    def _emit_settings_topmost_hotkey_pressed(self):
        self.settings_topmost_hotkey_pressed.emit()

    @Slot()
    def _handle_settings_topmost_hotkey_pressed(self):
        if not self._settings_topmost_hotkey_armed:
            return

        self._settings_topmost_hotkey_armed = False
        self._toggle_main_window_visibility()
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

    def _set_hovered(self, hovered):
        self._show_corner_lines = hovered
        self.label.set_corner_lines_visible(hovered)

    def enterEvent(self, event):
        self._set_hovered(True)
        if self._drag_mode is None:
            self._update_hover_cursor(self.mapFromGlobal(QCursor.pos()))
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._set_hovered(False)
        if self._drag_mode is None:
            if self._macos_cursor is not None:
                self._macos_cursor.mouse_exited()
            self.unsetCursor()
            self.label.unsetCursor()
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
        if self.isVisible():
            if self._macos_rules is not None:
                self._macos_rules.order_front_without_activation()
            else:
                self.raise_()
        self.hide_timer.start(10000)

    def _toggle_main_window_visibility(self):
        self.main_window_visibility_toggle_requested.emit()

    def set_settings_topmost_hotkey(self, hotkey):
        if hotkey == self.settings_topmost_hotkey:
            return True

        candidate = GlobalHotkey(hotkey, self._emit_settings_topmost_hotkey_pressed)
        if not candidate.start():
            return False

        self._settings_topmost_hotkey.stop()
        self._settings_topmost_hotkey = candidate
        self.settings_topmost_hotkey = hotkey
        return True

    def closeEvent(self, event):
        if self._macos_cursor is not None:
            self._macos_cursor.stop()
        if self._macos_rules is not None:
            self._macos_rules.stop()
        self._settings_topmost_hotkey.stop()
        super().closeEvent(event)

    def set_mode(self, scan):
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        if self._drag_mode is None:
            self._update_hover_cursor(self.mapFromGlobal(QCursor.pos()))
        if scan:
            self.hide_timer.start(10000)
        else:
            self.hide_timer.stop()
            self.label.setText(_("Translation will appear here."))

    def _resize_edges_at(self, position):
        edges = Qt.Edges()
        if not self.rect().contains(position):
            return edges
        if position.x() < self.RESIZE_MARGIN:
            edges |= Qt.LeftEdge
        elif position.x() >= self.width() - self.RESIZE_MARGIN:
            edges |= Qt.RightEdge
        if position.y() < self.RESIZE_MARGIN:
            edges |= Qt.TopEdge
        elif position.y() >= self.height() - self.RESIZE_MARGIN:
            edges |= Qt.BottomEdge
        return edges

    @staticmethod
    def _cursor_for_edges(edges):
        horizontal = bool(edges & (Qt.LeftEdge | Qt.RightEdge))
        vertical = bool(edges & (Qt.TopEdge | Qt.BottomEdge))
        if horizontal and vertical:
            if bool(edges & Qt.LeftEdge) == bool(edges & Qt.TopEdge):
                return Qt.SizeFDiagCursor
            return Qt.SizeBDiagCursor
        if horizontal:
            return Qt.SizeHorCursor
        if vertical:
            return Qt.SizeVerCursor
        return Qt.SizeAllCursor

    def _set_interaction_cursor(self, cursor):
        self.setCursor(cursor)
        # Keep the full-size text child consistent with its interactive parent.
        self.label.setCursor(cursor)
        if self._macos_cursor is not None:
            self._macos_cursor.apply_cursor(cursor)

    def _update_hover_cursor(self, position):
        cursor = (
            self._cursor_for_edges(self._resize_edges_at(position))
            if self.rect().contains(position)
            else Qt.ArrowCursor
        )
        self._set_interaction_cursor(cursor)

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            super().mousePressEvent(event)
            return
        self._drag_start_pos = event.globalPosition().toPoint()
        self._drag_start_geometry = self.geometry()
        self._drag_edges = self._resize_edges_at(event.position().toPoint())
        self._drag_mode = "resize" if self._drag_edges else "move"
        self._set_interaction_cursor(self._cursor_for_edges(self._drag_edges))
        event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_mode is None:
            self._update_hover_cursor(event.position().toPoint())
            return
        if self._drag_start_pos is None:
            return
        delta = event.globalPosition().toPoint() - self._drag_start_pos
        geometry = self._drag_start_geometry
        if self._drag_mode == "move":
            self.move(geometry.topLeft() + delta)
        else:
            # Anchor the opposite edges while enforcing the existing size limits.
            geometry = self._drag_start_geometry.adjusted(0, 0, 0, 0)
            min_width = max(self.MINIMUM_RESIZE_WIDTH, self.minimumWidth())
            min_height = max(self.MINIMUM_RESIZE_HEIGHT, self.minimumHeight())
            if self._drag_edges & Qt.LeftEdge:
                geometry.setLeft(min(geometry.left() + delta.x(), geometry.right() - min_width + 1))
            elif self._drag_edges & Qt.RightEdge:
                geometry.setWidth(max(min_width, geometry.width() + delta.x()))
            if self._drag_edges & Qt.TopEdge:
                geometry.setTop(min(geometry.top() + delta.y(), geometry.bottom() - min_height + 1))
            elif self._drag_edges & Qt.BottomEdge:
                geometry.setHeight(max(min_height, geometry.height() + delta.y()))
            self.setGeometry(geometry)
        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            super().mouseReleaseEvent(event)
            return
        self._drag_mode = None
        self._drag_edges = Qt.Edges()
        self._drag_start_pos = None
        self._drag_start_geometry = None
        self._update_hover_cursor(event.position().toPoint())
        event.accept()
