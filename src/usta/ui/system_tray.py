"""System tray actions backed by the control panel's shared window actions."""

import logging

from PySide6.QtCore import QObject, QRect, QTimer
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from usta.config import OS
from usta.i18n import _
from usta.ui.tray_hint import TrayHint

logger = logging.getLogger(__name__)


class SystemTray(QObject):
    def __init__(self, panel):
        super().__init__(panel)
        self.panel = panel
        self.menu = QMenu(panel)
        self.main_action = self.menu.addAction("", panel.toggle_main_window)
        self.overlay_action = self.menu.addAction("", panel.toggle_overlay)
        self.menu.addSeparator()
        self.start_action = self.menu.addAction(_("▶ Start"), panel.start)
        self.stop_action = self.menu.addAction(_("■ Stop"), panel.stop)
        self.menu.addSeparator()
        self.region_action = self.menu.addAction(_("Select Region"), panel.select_region)
        self.temporary_region_action = self.menu.addAction(
            _("Select Temporary Region"), panel._handle_temporary_region_hotkey_pressed
        )
        self.menu.addSeparator()
        self.quit_action = self.menu.addAction(_("Quit Application"), panel.request_quit)
        self.menu.aboutToShow.connect(self.refresh)
        self.icon = QSystemTrayIcon(panel.windowIcon(), self)
        self.icon.setToolTip("USTA")
        self.icon.setContextMenu(self.menu)
        self.refresh()
        self.icon.show()
        self.hint = TrayHint()
        self.destroyed.connect(self.hint.deleteLater)
        self._hint_shown = False
        self._hint_attempts = 0
        self.startup_timer = QTimer(self)
        self.startup_timer.setSingleShot(True)
        self.startup_timer.timeout.connect(self._show_startup_hint)
        self.startup_timer.start(500)
        if not self.available:
            logger.warning("System tray is unavailable; closing the main window will exit USTA.")

    def _show_startup_hint(self):
        self.startup_timer.stop()
        if self.panel._closing or self._hint_shown or not self.available:
            return
        if self.hint.show_at(self._icon_geometry()):
            self._hint_shown = True
        elif self._hint_attempts < 5:
            self._hint_attempts += 1
            self.startup_timer.start(200)

    def _icon_geometry(self):
        anchor = self.icon.geometry()
        if not anchor.isEmpty() or OS != "Darwin" or QGuiApplication.platformName() != "cocoa":
            return anchor
        try:
            import AppKit

            # Qt can return an empty tray rect on macOS. Read only our own
            # status-level windows through public AppKit APIs, without AX access.
            frame = AppKit.NSScreen.screens()[0].frame()
            top = frame.origin.y + frame.size.height
            candidates = []
            for window in AppKit.NSApp.windows():
                frame = window.frame()
                if (
                    window.level() == AppKit.NSStatusWindowLevel
                    and 0 < frame.size.width <= 128
                    and 0 < frame.size.height <= 64
                ):
                    candidates.append(
                        QRect(
                            round(frame.origin.x),
                            round(top - frame.origin.y - frame.size.height),
                            round(frame.size.width),
                            round(frame.size.height),
                        )
                    )
            screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
            if screen is not None:
                for candidate in candidates:
                    if screen.geometry().intersects(candidate):
                        return candidate
            if candidates:
                return candidates[0]
        except Exception as exc:
            logger.debug("Tray hint anchor unavailable: %s", exc)
        return anchor

    def close(self):
        self.startup_timer.stop()
        self.hint.close()
        self.icon.hide()

    @property
    def available(self):
        return QSystemTrayIcon.isSystemTrayAvailable()

    def refresh(self):
        panel = self.panel
        main_visible = panel.isVisible() and not panel.isMinimized()
        self.main_action.setText(_("Hide Main Window") if main_visible else _("Show Main Window"))
        self.overlay_action.setText(
            _("Hide Overlay") if panel.overlay.isVisible() else _("Show Overlay")
        )
        running = panel.worker.isRunning()
        self.start_action.setEnabled(not running and not panel._closing)
        self.stop_action.setEnabled(running and not panel._closing)
        selecting = panel._temporary_region_selecting or panel._region_selecting
        self.region_action.setEnabled(not selecting and not panel._closing)
        self.temporary_region_action.setEnabled(running and not selecting and not panel._closing)
