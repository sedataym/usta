import os
import sys
from PySide6.QtCore import Qt, QRect, QPoint, Signal, QObject, QEventLoop
from PySide6.QtGui import QPainter, QColor, QPen, QCursor
from PySide6.QtWidgets import QApplication, QWidget
from src.core.sniper.base_sniper import BaseSniper

class SelectionManager(QObject):
    """Manages the selection state across multiple monitors."""
    selectionChanged = Signal()
    selectionFinished = Signal(QRect)

    def __init__(self):
        super().__init__()
        self.start_pos = QPoint()
        self.end_pos = QPoint()
        self.is_selecting = False

    def startSelection(self, pos):
        self.start_pos = pos
        self.end_pos = pos
        self.is_selecting = True
        self.selectionChanged.emit()

    def updateSelection(self, pos):
        if self.is_selecting:
            self.end_pos = pos
            self.selectionChanged.emit()

    def finishSelection(self):
        if not self.is_selecting:
            return
        self.is_selecting = False
        rect = QRect(self.start_pos, self.end_pos).normalized()
        self.selectionFinished.emit(rect)

class OverlayWindow(QWidget):
    """An overlay window for a single screen."""
    def __init__(self, screen, manager):
        super().__init__()
        self.manager = manager
        self.screen_geometry = screen.geometry()
        
        flags = (
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        if sys.platform != "darwin":
            flags |= Qt.X11BypassWindowManagerHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._macos_hotkey_window = None
        if sys.platform == "darwin":
            from src.ui.macos_hotkeys import MacOSHotkeyWindow
            self.setAttribute(Qt.WA_ShowWithoutActivating)
            self.setAttribute(Qt.WA_MacAlwaysShowToolWindow)
            self._macos_hotkey_window = MacOSHotkeyWindow(self)
        
        self.setGeometry(self.screen_geometry)
        self.setCursor(Qt.CrossCursor)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        
        self.manager.selectionChanged.connect(self.update)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 128))

        if self.manager.is_selecting:
            global_rect = QRect(self.manager.start_pos, self.manager.end_pos).normalized()
            local_intersect = global_rect.intersected(self.screen_geometry)
            
            if not local_intersect.isEmpty():
                local_rect = local_intersect.translated(-self.screen_geometry.topLeft())
                painter.setCompositionMode(QPainter.CompositionMode_Clear)
                painter.fillRect(local_rect, Qt.transparent)
                painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
                painter.setPen(QPen(Qt.red, 2))
                painter.drawRect(local_rect)

    def mousePressEvent(self, event):
        self.setFocus()
        if event.button() == Qt.LeftButton:
            self.manager.startSelection(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        self.manager.updateSelection(event.globalPosition().toPoint())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.manager.finishSelection()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.manager.selectionFinished.emit(QRect())

    def closeEvent(self, event):
        if self._macos_hotkey_window is not None:
            self._macos_hotkey_window.stop()
        super().closeEvent(event)

class CoreSniper(BaseSniper):
    def __init__(self):
        super().__init__()
        self.detected_dpi = 1.0

    def get_region(self) -> QRect | None:
        """Selects a region on the screen using a native multi-monitor overlay."""

        manager = SelectionManager()
        loop = QEventLoop()
        result_rect = [None]

        def on_finished(rect):
            if rect.isValid() and rect.width() > 5 and rect.height() > 5:
                result_rect[0] = rect
            loop.quit()

        manager.selectionFinished.connect(on_finished)

        windows = []
        for screen in QApplication.screens():
            win = OverlayWindow(screen, manager)
            if win._macos_hotkey_window is not None:
                win._macos_hotkey_window.show(focus=False)
            else:
                win.show()
                win.activateWindow()
                win.raise_()
            windows.append(win)

        if sys.platform == "darwin" and windows:
            target = next((win for win in windows if win.screen_geometry.contains(QCursor.pos())), windows[0])
            target._macos_hotkey_window.focus()

        loop.exec()
        
        for win in windows:
            win.close()
            if sys.platform == "darwin":
                # Native helpers retain the widget in Python reference cycles.
                # Schedule C++ destruction on the GUI thread before a later OCR
                # allocation can collect those cycles on its worker thread.
                win.deleteLater()

        rect = result_rect[0]
        if rect is not None:
            # Detect which screen contains the center of the selection and get its DPI
            center = rect.center()
            for screen in QApplication.screens():
                if screen.geometry().contains(center):
                    self.detected_dpi = screen.devicePixelRatio()
                    break
            
        return rect
