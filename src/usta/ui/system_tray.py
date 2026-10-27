"""System tray actions backed by the control panel's shared window actions."""

import logging

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from usta.i18n import _

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
        if not self.available:
            logger.warning("System tray is unavailable; closing the main window will exit USTA.")

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
