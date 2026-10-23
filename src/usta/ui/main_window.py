import logging
import os

from PySide6.QtCore import QSignalBlocker, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QColorDialog,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from usta.application.controller import ApplicationController
from usta.application.hotkey_controller import HotkeyController
from usta.application.region_controller import RegionController
from usta.application.worker import OCRWorker
from usta.config import (
    OS,
    SETTINGS_TOPMOST_HOTKEY,
    TEMPORARY_REGION_HOTKEY,
    get_language_code,
)
from usta.i18n import _
from usta.ui.overlay_window import TransparentOverlay
from usta.ui.region_selection import SniperFactory
from usta.ui.settings_presenter import SettingsPresenter
from usta.ui.tabs import (
    AboutTab,
    AppearanceTab,
    HotkeyTab,
    OCRTab,
    SaveTab,
    StatusTab,
    TranslationTab,
)

logger = logging.getLogger(__name__)


class ControlPanel(QWidget):
    temporary_region_hotkey_pressed = Signal()

    def __init__(self):
        super().__init__()
        self._loading_settings = True
        self.settings_presenter = SettingsPresenter(self)
        self.worker = OCRWorker()
        self.overlay = TransparentOverlay()
        self.controller = ApplicationController(self.worker)
        self.region_controller = RegionController(self.controller, self)
        self.region_controller.changed.connect(self._region_changed)
        self._temporary_region_selecting = False
        self._temporary_region_hotkey_armed = True
        self.settings_topmost_hotkey = SETTINGS_TOPMOST_HOTKEY
        self.temporary_region_hotkey = TEMPORARY_REGION_HOTKEY
        self.hotkey_controller = HotkeyController(
            self.temporary_region_hotkey,
            self._emit_temporary_region_hotkey_pressed,
        )
        self.temporary_region_hotkey_pressed.connect(self._handle_temporary_region_hotkey_pressed)
        self.setWindowTitle("USTA")

        # Set window icon
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "usta.png")
        self.setWindowIcon(QIcon(icon_path))

        # Disable maximization
        self.setWindowFlags(self.windowFlags() | Qt.MSWindowsFixedSizeDialogHint)
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, False)
        self._macos_hotkey_window = None
        if OS == "Darwin":
            from usta.ui.platform.macos.hotkeys import MacOSHotkeyWindow

            # A decorated NSPanel can join another app's fullscreen Space.
            self.setWindowFlags((self.windowFlags() & ~Qt.WindowType_Mask) | Qt.Tool)
            self.setAttribute(Qt.WA_MacAlwaysShowToolWindow, True)
            self.setAttribute(Qt.WA_ShowWithoutActivating, True)
            self._macos_hotkey_window = MacOSHotkeyWindow(self)
        self._normal_window_flags = self.windowFlags()

        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QVBoxLayout.SetFixedSize)  # Fixed size according to content

        # --- Tabs ---
        self.tabs = QTabWidget()
        self.api_keys = {}
        self.dpi_locked = False
        self.ocr_tab = OCRTab()
        self.translation_tab = TranslationTab()
        self.appearance_tab = AppearanceTab()
        self.hotkey_tab = HotkeyTab()
        self.save_tab = SaveTab()
        self.status_tab = StatusTab()
        self.about_tab = AboutTab()
        self.ocr_tab.engine_changed.connect(self.controller.set_engine)
        self.ocr_tab.screen_engine_changed.connect(self.controller.set_screenshot_engine)
        self.ocr_tab.changed.connect(self.save_settings)
        self.ocr_tab.dpi_changed.connect(self.on_dpi_scale_changed)
        self.ocr_tab.toggle_dpi_requested.connect(self._toggle_dpi_lock)
        self.translation_tab.translator_changed.connect(self.controller.set_translator)
        self.translation_tab.changed.connect(self.save_settings)
        self.translation_tab.translator_selected.connect(
            self.settings_presenter.on_translator_changed
        )
        self.translation_tab.language_changed.connect(self.update_languages)
        self.translation_tab.api_key_changed.connect(self.settings_presenter.on_api_key_changed)
        self.appearance_tab.font_changed.connect(self.on_font_changed)
        self.appearance_tab.font_size_changed.connect(self.on_font_size_changed)
        self.appearance_tab.text_color_requested.connect(self.choose_color)
        self.appearance_tab.background_color_requested.connect(self.choose_bg_color)
        self.appearance_tab.opacity_changed.connect(self.on_bg_opacity_changed)
        self.hotkey_tab.settings_hotkey_changed.connect(self.on_settings_topmost_hotkey_changed)
        self.hotkey_tab.region_hotkey_changed.connect(self.on_temporary_region_hotkey_changed)
        self.hotkey_tab.reset_settings_requested.connect(self.reset_settings_topmost_hotkey)
        self.hotkey_tab.reset_region_requested.connect(self.reset_temporary_region_hotkey)
        self.save_tab.save_requested.connect(self.settings_presenter.save_preset)
        self.save_tab.load_requested.connect(self.settings_presenter.load_preset)
        self.save_tab.delete_requested.connect(self.settings_presenter.delete_preset)

        self.tabs.addTab(self.status_tab, _("Status"))
        self.tabs.addTab(self.ocr_tab, _("OCR"))
        self.tabs.addTab(self.translation_tab, _("Translation"))
        self.tabs.addTab(self.appearance_tab, _("Appearance"))
        self.tabs.addTab(self.save_tab, _("Save"))
        self.tabs.addTab(self.hotkey_tab, _("Hotkeys"))
        self.tabs.addTab(self.about_tab, _("About"))

        layout.addWidget(self.tabs)

        # --- Performance Indicator (outside tabs) ---
        layout.addWidget(QLabel(_("<br><b>Performance</b>")))
        self.perf_bar = QProgressBar()
        self.perf_bar.setRange(0, 100)
        self.perf_bar.setValue(0)
        self.perf_bar.setTextVisible(False)
        self.perf_bar.setFixedHeight(10)
        layout.addWidget(self.perf_bar)

        # --- Controls (outside tabs) ---
        layout.addWidget(QLabel(_("<b>Controls</b>")))
        self.btn_reg = QPushButton(_("🖼 Select Region"))
        self.btn_reg.setStyleSheet(
            "background-color: #1565C0; color: white; font-weight: bold; padding: 10px;"
        )
        self.btn_reg.clicked.connect(self.select_region)
        layout.addWidget(self.btn_reg)

        self.btn_start = QPushButton(_("▶ Start"))
        self.btn_start.setStyleSheet(
            "background-color: #2E7D32; color: white; font-weight: bold; padding: 10px;"
        )
        self.btn_start.clicked.connect(self.start)
        layout.addWidget(self.btn_start)

        self.btn_stop = QPushButton(_("■ Stop"))
        self.btn_stop.setStyleSheet(
            "background-color: #C62828; color: white; font-weight: bold; padding: 10px;"
        )
        self.btn_stop.clicked.connect(self.stop)
        layout.addWidget(self.btn_stop)

        self.worker.error_occurred.connect(self.overlay.update_text)
        self.worker.new_translation.connect(self.overlay.update_text)
        self.worker.performance_update.connect(self.update_performance_bar)
        self.worker.running_status.connect(self.update_system_status)
        self.overlay.main_window_topmost_requested.connect(self.set_settings_always_on_top)
        self._settings_always_on_top = False

        # Load settings or set defaults
        self.load_settings()

        # Initialize status tab with current rect
        self.update_rect_label()
        self.refresh_preset_list()
        self.show()

        # Align overlay to the right of the control panel with a slight delay
        # to ensure the window manager has placed the main window.
        QTimer.singleShot(100, self.align_overlay)

    def align_overlay(self):
        """Positions the overlay window next to the main window."""
        # Force a refresh of the window's geometry information
        QApplication.processEvents()

        # Get the global position of the main window's frame
        rect = self.frameGeometry()
        target_x = rect.right() + 10
        target_y = rect.top()

        # Move and then show the overlay
        self.overlay.move(target_x, target_y)
        self.overlay.show()

        # For windows bypassing the WM, move after show is often more reliable
        self.overlay.move(target_x, target_y)

    @Slot(bool)
    def set_settings_always_on_top(self, enabled):
        """Toggle the control panel's game-friendly topmost state from the overlay."""
        self._settings_always_on_top = enabled

        if self._macos_hotkey_window is not None:
            if enabled:
                self._macos_hotkey_window.show()
            else:
                self._macos_hotkey_window.lower()
            return

        if enabled:
            # Keep the control panel decorated by the window manager.
            # Qt.Tool / Qt.X11BypassWindowManagerHint can remove borders on some WMs,
            # so the settings window uses normal flags plus always-on-top here.
            self.setWindowFlags(self._normal_window_flags | Qt.WindowStaysOnTopHint)
            self.setWindowFlag(Qt.WindowMaximizeButtonHint, False)
            self.setAttribute(Qt.WA_ShowWithoutActivating, True)
            self.show()
            self.raise_()
            self.activateWindow()
        else:
            self.setAttribute(Qt.WA_ShowWithoutActivating, False)
            self.setWindowFlags(self._normal_window_flags)
            self.setWindowFlag(Qt.WindowMaximizeButtonHint, False)
            self.show()
            self.lower()

    def on_font_changed(self, font):
        self.overlay.set_font_family(font.family())
        self.save_settings()

    def on_font_size_changed(self, size):
        self.overlay.set_font_size(size)
        self.save_settings()

    def on_dpi_scale_changed(self, percent_value):
        self.controller.dpi_scale = percent_value / 100.0
        self.dpi_locked = True
        self.ocr_tab.dpi_lock_label.setText("🔒")
        self.ocr_tab.dpi_lock_label.setToolTip(_("DPI locked (click to unlock)"))
        self.save_settings()

    def _toggle_dpi_lock(self, event):
        self.dpi_locked = not self.dpi_locked
        if self.dpi_locked:
            self.ocr_tab.dpi_lock_label.setText("🔒")
            self.ocr_tab.dpi_lock_label.setToolTip(_("DPI locked (click to unlock)"))
        else:
            self.ocr_tab.dpi_lock_label.setText("🔓")
            self.ocr_tab.dpi_lock_label.setToolTip(_("DPI unlocked (click to lock)"))
        return True

    def on_bg_opacity_changed(self, opacity):
        self.overlay.set_bg_opacity(opacity)
        self.save_settings()

    def _apply_saved_hotkeys(self, settings_topmost_hotkey, temporary_region_hotkey):
        self._set_settings_topmost_hotkey(settings_topmost_hotkey, save=False, show_error=False)
        self._set_temporary_region_hotkey(temporary_region_hotkey, save=False, show_error=False)
        self._sync_hotkey_buttons()

    def _sync_hotkey_buttons(self):
        if hasattr(self.hotkey_tab, "settings_topmost_hotkey_button"):
            self.hotkey_tab.settings_topmost_hotkey_button.set_hotkey(self.settings_topmost_hotkey)
        if hasattr(self.hotkey_tab, "temporary_region_hotkey_button"):
            self.hotkey_tab.temporary_region_hotkey_button.set_hotkey(self.temporary_region_hotkey)

    def _set_settings_topmost_hotkey(self, hotkey, save=True, show_error=True):
        if self.overlay.set_settings_topmost_hotkey(hotkey):
            self.settings_topmost_hotkey = hotkey
            self._sync_hotkey_buttons()
            if save:
                self.save_settings()
            return True

        if show_error:
            QMessageBox.warning(
                self,
                _("Invalid shortcut"),
                _("Could not register this shortcut. The previous shortcut is still active."),
            )
        self._sync_hotkey_buttons()
        return False

    def _set_temporary_region_hotkey(self, hotkey, save=True, show_error=True):
        if hotkey == self.temporary_region_hotkey:
            self._sync_hotkey_buttons()
            return True

        if self.hotkey_controller.set_hotkey(hotkey):
            self.temporary_region_hotkey = hotkey
            self._sync_hotkey_buttons()
            if save:
                self.save_settings()
            return True

        if show_error:
            QMessageBox.warning(
                self,
                _("Invalid shortcut"),
                _("Could not register this shortcut. The previous shortcut is still active."),
            )
        self._sync_hotkey_buttons()
        return False

    def on_settings_topmost_hotkey_changed(self, hotkey):
        self._set_settings_topmost_hotkey(hotkey)

    def on_temporary_region_hotkey_changed(self, hotkey):
        self._set_temporary_region_hotkey(hotkey)

    def reset_settings_topmost_hotkey(self):
        self._set_settings_topmost_hotkey(SETTINGS_TOPMOST_HOTKEY)

    def reset_temporary_region_hotkey(self):
        self._set_temporary_region_hotkey(TEMPORARY_REGION_HOTKEY)

    def update_system_status(self, is_running):
        if is_running:
            self.status_tab.system_indicator.setStyleSheet(
                "background-color: #2E7D32; border-radius: 8px;"
            )
            self.status_tab.system_status_label.setText(_("Running"))
        else:
            self.status_tab.system_indicator.setStyleSheet(
                "background-color: #C62828; border-radius: 8px;"
            )
            self.status_tab.system_status_label.setText(_("Stopped"))
            self.overlay.set_mode(False)
            self.perf_bar.setValue(0)
            self.perf_bar.setStyleSheet("")

    def update_rect_label(self):
        r = self.controller.capture_rect
        self.status_tab.rect_label_status.setText(
            _("Region: X:{x} Y:{y}  {w}×{h}").format(x=r.x(), y=r.y(), w=r.width(), h=r.height())
        )

    def update_performance_bar(self, duration):
        # Inverse logic: 0.5s -> %100 (Best), 3.0s -> %0 (Worst)
        if not self.worker.isRunning():
            return
        percent = int(100 - (((duration - 0.5) / 2.5) * 100))
        percent = max(0, min(100, percent))

        self.perf_bar.setValue(percent)

        # Color determination based on percentage (Health bar logic)
        if percent >= 75:
            color = "#2E7D32"  # Green (Great)
        elif percent >= 35:
            color = "#F9A825"  # Yellow/Orange (Normal)
        else:
            color = "#C62828"  # Red (Poor)

        self.perf_bar.setStyleSheet(f"""
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 2px;
            }}
            QProgressBar {{
                border: 1px solid gray;
                border-radius: 3px;
                background: #E0E0E0;
            }}
        """)

    def update_languages(self):
        source_code = get_language_code(self.translation_tab.combo_source.currentText(), "en")
        target_code = get_language_code(self.translation_tab.combo_target.currentText(), "tr")
        self.controller.set_languages(source_code, target_code)
        self.save_settings()

    def choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            color_name = color.name()
            self.overlay.set_font_color(color_name)
            self.appearance_tab.color_sample.setStyleSheet(
                f"background-color: {color_name}; border: 1px solid gray; border-radius: 4px;"
            )
            self.save_settings()

    def choose_bg_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            color_name = color.name()
            self.overlay.set_bg_color(color_name)
            self.appearance_tab.bg_color_sample.setStyleSheet(
                f"background-color: {color_name}; border: 1px solid gray; border-radius: 4px;"
            )
            self.save_settings()

    def _emit_temporary_region_hotkey_pressed(self):
        self.temporary_region_hotkey_pressed.emit()

    @Slot()
    def _handle_temporary_region_hotkey_pressed(self):
        if (
            not self.worker.isRunning()
            or self._temporary_region_selecting
            or not self._temporary_region_hotkey_armed
        ):
            return

        self._temporary_region_hotkey_armed = False
        QTimer.singleShot(200, self._rearm_temporary_region_hotkey)
        QTimer.singleShot(200, self.select_temporary_region)

    def _rearm_temporary_region_hotkey(self):
        self._temporary_region_hotkey_armed = True

    def _get_selected_region_and_dpi(self):
        QApplication.processEvents()

        sniper = SniperFactory.get_engine()
        rect = sniper.get_region()
        if not rect:
            return None, None

        detected_dpi = getattr(sniper, "detected_dpi", None)
        return rect, detected_dpi

    def _region_changed(self, text):
        self.overlay.label.setText(text)
        self.update_rect_label()

    def _apply_main_region(self, rect, dpi_scale=None):
        if self.dpi_locked:
            dpi_scale = None
        if dpi_scale is not None:
            blocker = QSignalBlocker(self.ocr_tab.dpi_scale_spin)
            self.ocr_tab.dpi_scale_spin.setValue(dpi_scale * 100)
            del blocker
        self.region_controller.apply_main_region(rect, dpi_scale)
        self.save_settings()

    def _apply_temporary_region(self, rect, dpi_scale=None):
        self.region_controller.apply_temporary_region(rect, None if self.dpi_locked else dpi_scale)

    def _restore_main_region(self):
        self.region_controller.restore_main_region()

    def select_temporary_region(self):
        self._temporary_region_selecting = True
        try:
            rect, detected_dpi = self._get_selected_region_and_dpi()
        finally:
            self._temporary_region_selecting = False

        if rect:
            self._apply_temporary_region(rect, detected_dpi)

    def select_region(self):
        QTimer.singleShot(200, self._select_region_now)

    def _select_region_now(self):
        rect, detected_dpi = self._get_selected_region_and_dpi()
        if rect:
            self._apply_main_region(rect, detected_dpi)

    def start(self):
        self.overlay.set_mode(True)
        if not self.worker.isRunning():
            self.controller.start()

    def stop(self):
        self.controller.stop()
        self.overlay.set_mode(False)
        self.perf_bar.setValue(0)
        self.perf_bar.setStyleSheet("")

    def closeEvent(self, event):
        if self.worker.isRunning():
            event.ignore()
            self.worker.finished.connect(self.close)
            self.controller.stop()
            return
        self.worker.close()
        if self._macos_hotkey_window is not None:
            self._macos_hotkey_window.stop()
        self.region_controller.restore_timer.stop()
        self.hotkey_controller.close()
        self.controller.stop()
        self.overlay.close()
        super().closeEvent(event)
        if self._macos_hotkey_window is not None and event.isAccepted():
            # Qt.Tool panels do not trigger quitOnLastWindowClosed.
            QApplication.instance().quit()

    # ---------- API Key Helpers ----------

    # ---------- Preset Management ----------

    def save_settings(self):
        self.settings_presenter.save_settings()

    def load_settings(self):
        self.settings_presenter.load_settings()

    def refresh_preset_list(self):
        self.settings_presenter.refresh_preset_list()
