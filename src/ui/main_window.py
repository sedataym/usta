import time
import pickle
import os
import json
from PySide6.QtCore import Qt, QRect, QPoint, QTimer, Signal, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QApplication, QColorDialog, QProgressBar, QTabWidget, QMessageBox, QDialog, QFormLayout, QLineEdit, QPlainTextEdit, QListWidget, QDialogButtonBox
from src.core.worker import OCRWorker
from src.ui.overlay_window import TransparentOverlay
from src.core.sniper import SniperFactory
from src.config import LANGUAGES, SETTINGS_FILE, PRESETS_FILE, CUSTOM_OCR_APIS_FILE, DPI_SCALE_DEFAULT, SETTINGS_TOPMOST_HOTKEY, TEMPORARY_REGION_HOTKEY, OCR_ENGINES, get_language_code
from src.core.shortcut import GlobalHotkey
from src.i18n import _
from src.ui.tabs import (
    build_about_tab,
    build_appearance_tab,
    build_ocr_tab,
    build_save_tab,
    build_hotkey_tab,
    build_status_tab,
    build_translation_tab,
)

class ControlPanel(QWidget):
    temporary_region_hotkey_pressed = Signal()

    def __init__(self):
        super().__init__()
        self.worker = OCRWorker()
        self.overlay = TransparentOverlay()
        self._main_capture_rect = QRect(self.worker.capture_rect)
        self._main_dpi_scale = self.worker.dpi_scale
        self._temporary_region_active = False
        self._temporary_region_selecting = False
        self._temporary_region_restore_timer = QTimer(self)
        self._temporary_region_restore_timer.setSingleShot(True)
        self._temporary_region_restore_timer.timeout.connect(self._restore_main_region)
        self._temporary_region_hotkey_armed = True
        self.settings_topmost_hotkey = SETTINGS_TOPMOST_HOTKEY
        self.temporary_region_hotkey = TEMPORARY_REGION_HOTKEY
        self._temporary_region_hotkey = GlobalHotkey(
            self.temporary_region_hotkey,
            self._emit_temporary_region_hotkey_pressed,
        )
        self.temporary_region_hotkey_pressed.connect(self._handle_temporary_region_hotkey_pressed)
        self._temporary_region_hotkey.start()
        self.setWindowTitle("USTA")
        
        # Set window icon
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "usta.png")
        self.setWindowIcon(QIcon(icon_path))
        
        # Disable maximization
        self.setWindowFlags(self.windowFlags() | Qt.MSWindowsFixedSizeDialogHint)
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, False)
        self._normal_window_flags = self.windowFlags()
        
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QVBoxLayout.SetFixedSize) # Fixed size according to content
        
        # --- Tabs ---
        self.tabs = QTabWidget()
        self.tabs.addTab(build_status_tab(self), _("Status"))
        self.tabs.addTab(build_ocr_tab(self), _("OCR"))
        self.tabs.addTab(build_translation_tab(self), _("Translation"))
        self.tabs.addTab(build_appearance_tab(self), _("Appearance"))
        self.tabs.addTab(build_save_tab(self), _("Save"))
        self.tabs.addTab(build_hotkey_tab(self), _("Hotkeys"))
        self.tabs.addTab(build_about_tab(self), _("About"))

        
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
        self.btn_reg.setStyleSheet("background-color: #1565C0; color: white; font-weight: bold; padding: 10px;")
        self.btn_reg.clicked.connect(self.select_region)
        layout.addWidget(self.btn_reg)
        
        self.btn_start = QPushButton(_("▶ Start"))
        self.btn_start.setStyleSheet("background-color: #2E7D32; color: white; font-weight: bold; padding: 10px;")
        self.btn_start.clicked.connect(self.start)
        layout.addWidget(self.btn_start)
        
        self.btn_stop = QPushButton(_("■ Stop"))
        self.btn_stop.setStyleSheet("background-color: #C62828; color: white; font-weight: bold; padding: 10px;")
        self.btn_stop.clicked.connect(self.stop)
        layout.addWidget(self.btn_stop)
        
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
        self.worker.dpi_scale = percent_value / 100.0
        self.dpi_locked = True
        self.dpi_lock_label.setText("🔒")
        self.dpi_lock_label.setToolTip(_("DPI locked (click to unlock)"))
        self.save_settings()

    def _toggle_dpi_lock(self, event):
        self.dpi_locked = not self.dpi_locked
        if self.dpi_locked:
            self.dpi_lock_label.setText("🔒")
            self.dpi_lock_label.setToolTip(_("DPI locked (click to unlock)"))
        else:
            self.dpi_lock_label.setText("🔓")
            self.dpi_lock_label.setToolTip(_("DPI unlocked (click to lock)"))
        return True

    def on_bg_opacity_changed(self, opacity):
        self.overlay.set_bg_opacity(opacity)
        self.save_settings()

    def save_settings(self):
        settings = {
            "ocr_engine": self.combo_ocr.currentText(),
            "translator_engine": self.combo_translator.currentText(),
            "source_lang": self.combo_source.currentText(),
            "target_lang": self.combo_target.currentText(),
            "font_family": self.font_picker.currentFont().family(),
            "font_size": self.font_size_spin.value(),
            "font_color": self.overlay.font_color,
            "bg_color": self.overlay.bg_color,
            "bg_opacity": self.overlay.bg_opacity,
            "translator_api_keys": self.api_keys,
            "capture_rect": (self.worker.capture_rect.x(), self.worker.capture_rect.y(), 
                            self.worker.capture_rect.width(), self.worker.capture_rect.height()),
            "dpi_scale": self.worker.dpi_scale,
            "screenshot_engine": self.combo_screenshot.currentText(),
            "settings_topmost_hotkey": self.settings_topmost_hotkey,
            "temporary_region_hotkey": self.temporary_region_hotkey,
        }
        try:
            with open(SETTINGS_FILE, "wb") as f:
                pickle.dump(settings, f)
            print("Settings saved.")
        except Exception as e:
            print(f"Settings save error: {e}")

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "rb") as f:
                    s = pickle.load(f)
                
                # Update UI elements
                self._refresh_ocr_combo(selected=s.get("ocr_engine", self._default_ocr_engine()))
                self.combo_translator.setCurrentText(s.get("translator_engine", "Google"))
                self.combo_source.setCurrentText(s.get("source_lang", "English"))
                self.combo_target.setCurrentText(s.get("target_lang", "Turkish"))
                
                font_family = s.get("font_family", "Arial")
                self.font_picker.setCurrentFont(font_family)
                self.overlay.set_font_family(font_family)
                
                font_size = s.get("font_size", 20)
                self.font_size_spin.setValue(font_size)
                self.overlay.set_font_size(font_size)
                
                font_color = s.get("font_color", "white")
                self.overlay.set_font_color(font_color)
                self.color_sample.setStyleSheet(f"background-color: {font_color}; border: 1px solid gray; border-radius: 4px;")
                
                bg_color = s.get("bg_color", "#000000")
                self.overlay.set_bg_color(bg_color)
                self.bg_color_sample.setStyleSheet(f"background-color: {bg_color}; border: 1px solid gray; border-radius: 4px;")
                
                bg_opacity = s.get("bg_opacity", 180)
                self.bg_opacity_spin.setValue(bg_opacity)
                self.overlay.set_bg_opacity(bg_opacity)
                
                # Load DPI scale
                dpi_scale = s.get("dpi_scale", DPI_SCALE_DEFAULT)
                self.dpi_scale_spin.blockSignals(True)
                self.dpi_scale_spin.setValue(dpi_scale * 100)
                self.dpi_scale_spin.blockSignals(False)
                self.worker.dpi_scale = dpi_scale
                self._main_dpi_scale = self.worker.dpi_scale

                rect = s.get("capture_rect")
                if rect:
                    self.worker.set_rect(QRect(rect[0], rect[1], rect[2], rect[3]))
                    self._main_capture_rect = QRect(self.worker.capture_rect)
                    self.update_rect_label()
                
                # Load screenshot engine
                screenshot_engine = s.get("screenshot_engine", "Portal")
                self.combo_screenshot.setCurrentText(screenshot_engine)
                self.worker.set_screenshot_engine(screenshot_engine)

                # Load API keys
                self.api_keys = s.get("translator_api_keys", {})
                self._apply_api_key_for_current_engine()

                self._apply_saved_hotkeys(
                    s.get("settings_topmost_hotkey", SETTINGS_TOPMOST_HOTKEY),
                    s.get("temporary_region_hotkey", TEMPORARY_REGION_HOTKEY),
                )

                self.update_languages()
                print("Settings loaded.")
                return
            except Exception as e:
                print(f"Settings load error: {e}")
        
        # If file not exists or error occurs, set defaults
        self._refresh_ocr_combo(selected=self._default_ocr_engine())
        self._apply_saved_hotkeys(SETTINGS_TOPMOST_HOTKEY, TEMPORARY_REGION_HOTKEY)
        self.update_languages()

    def _apply_saved_hotkeys(self, settings_topmost_hotkey, temporary_region_hotkey):
        self._set_settings_topmost_hotkey(settings_topmost_hotkey, save=False, show_error=False)
        self._set_temporary_region_hotkey(temporary_region_hotkey, save=False, show_error=False)
        self._sync_hotkey_buttons()

    def _sync_hotkey_buttons(self):
        if hasattr(self, "settings_topmost_hotkey_button"):
            self.settings_topmost_hotkey_button.set_hotkey(self.settings_topmost_hotkey)
        if hasattr(self, "temporary_region_hotkey_button"):
            self.temporary_region_hotkey_button.set_hotkey(self.temporary_region_hotkey)

    def _set_settings_topmost_hotkey(self, hotkey, save=True, show_error=True):
        if self.overlay.set_settings_topmost_hotkey(hotkey):
            self.settings_topmost_hotkey = hotkey
            self._sync_hotkey_buttons()
            if save:
                self.save_settings()
            return True

        if show_error:
            QMessageBox.warning(self, _("Invalid shortcut"), _("Could not register this shortcut. The previous shortcut is still active."))
        self._sync_hotkey_buttons()
        return False

    def _set_temporary_region_hotkey(self, hotkey, save=True, show_error=True):
        if hotkey == self.temporary_region_hotkey:
            self._sync_hotkey_buttons()
            return True

        candidate = GlobalHotkey(hotkey, self._emit_temporary_region_hotkey_pressed)
        if candidate.start():
            self._temporary_region_hotkey.stop()
            self._temporary_region_hotkey = candidate
            self.temporary_region_hotkey = hotkey
            self._sync_hotkey_buttons()
            if save:
                self.save_settings()
            return True

        if show_error:
            QMessageBox.warning(self, _("Invalid shortcut"), _("Could not register this shortcut. The previous shortcut is still active."))
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
            self.system_indicator.setStyleSheet(
                "background-color: #2E7D32; border-radius: 8px;"
            )
            self.system_status_label.setText("Running")
        else:
            self.system_indicator.setStyleSheet(
                "background-color: #C62828; border-radius: 8px;"
            )
            self.system_status_label.setText("Stopped")
            self.overlay.set_mode(False)
            self.perf_bar.setValue(0)
            self.perf_bar.setStyleSheet("")

    def update_rect_label(self):
        r = self.worker.capture_rect
        self.rect_label_status.setText(
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
            color = "#2E7D32" # Green (Great)
        elif percent >= 35:
            color = "#F9A825" # Yellow/Orange (Normal)
        else:
            color = "#C62828" # Red (Poor)
            
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
        source_code = get_language_code(self.combo_source.currentText(), "en")
        target_code = get_language_code(self.combo_target.currentText(), "tr")
        self.worker.set_languages(source_code, target_code)
        self.save_settings()

    def choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            color_name = color.name()
            self.overlay.set_font_color(color_name)
            self.color_sample.setStyleSheet(f"background-color: {color_name}; border: 1px solid gray; border-radius: 4px;")
            self.save_settings()

    def choose_bg_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            color_name = color.name()
            self.overlay.set_bg_color(color_name)
            self.bg_color_sample.setStyleSheet(f"background-color: {color_name}; border: 1px solid gray; border-radius: 4px;")
            self.save_settings()

    def _emit_temporary_region_hotkey_pressed(self):
        self.temporary_region_hotkey_pressed.emit()

    @Slot()
    def _handle_temporary_region_hotkey_pressed(self):
        if not self.worker.isRunning() or self._temporary_region_selecting or not self._temporary_region_hotkey_armed:
            return

        self._temporary_region_hotkey_armed = False
        QTimer.singleShot(200, self._rearm_temporary_region_hotkey)
        self.select_temporary_region()

    def _rearm_temporary_region_hotkey(self):
        self._temporary_region_hotkey_armed = True

    def _get_selected_region_and_dpi(self):
        QApplication.processEvents()
        time.sleep(0.2)

        sniper = SniperFactory.get_engine()
        rect = sniper.get_region()
        if not rect:
            return None, None

        detected_dpi = getattr(sniper, "detected_dpi", None)
        return rect, detected_dpi

    def _apply_main_region(self, rect, dpi_scale=None):
        if not self.dpi_locked and dpi_scale is not None:
            self.dpi_scale_spin.blockSignals(True)
            self.dpi_scale_spin.setValue(dpi_scale * 100)
            self.dpi_scale_spin.blockSignals(False)
            self.worker.dpi_scale = dpi_scale

        self.worker.set_rect(rect)
        self._main_capture_rect = QRect(self.worker.capture_rect)
        self._main_dpi_scale = self.worker.dpi_scale
        self.overlay.label.setText(f"Region: {rect.x()},{rect.y()} {rect.width()}x{rect.height()}")
        self.update_rect_label()
        self.save_settings()

    def _apply_temporary_region(self, rect, dpi_scale=None):
        if not self._temporary_region_active:
            self._main_capture_rect = QRect(self.worker.capture_rect)
            self._main_dpi_scale = self.worker.dpi_scale

        if not self.dpi_locked and dpi_scale is not None:
            self.worker.dpi_scale = dpi_scale

        self.worker.set_rect(rect)
        self._temporary_region_active = True
        self._temporary_region_restore_timer.start(10_000)
        self.overlay.label.setText(f"Temporary Region: {rect.x()},{rect.y()} {rect.width()}x{rect.height()} (10s)")
        self.update_rect_label()

    def _restore_main_region(self):
        if not self._temporary_region_active:
            return

        self.worker.dpi_scale = self._main_dpi_scale
        self.worker.set_rect(self._main_capture_rect)
        self._temporary_region_active = False
        self.overlay.label.setText(
            f"Region: {self._main_capture_rect.x()},{self._main_capture_rect.y()} "
            f"{self._main_capture_rect.width()}x{self._main_capture_rect.height()}"
        )
        self.update_rect_label()

    def select_temporary_region(self):
        self._temporary_region_selecting = True
        try:
            rect, detected_dpi = self._get_selected_region_and_dpi()
        finally:
            self._temporary_region_selecting = False

        if rect:
            self._apply_temporary_region(rect, detected_dpi)

    def select_region(self):
        rect, detected_dpi = self._get_selected_region_and_dpi()
        if rect:
            self._temporary_region_restore_timer.stop()
            self._temporary_region_active = False
            self._apply_main_region(rect, detected_dpi)

    def start(self): 
        self.overlay.set_mode(True)
        if not self.worker.isRunning():
            self.worker.start()

    def stop(self):
        self.worker.stop()
        self.overlay.set_mode(False)
        self.perf_bar.setValue(0)
        self.perf_bar.setStyleSheet("")

    def closeEvent(self, event):
        self._temporary_region_restore_timer.stop()
        self._temporary_region_hotkey.stop()
        self.worker.stop()
        self.overlay.close()
        super().closeEvent(event)

    # ---------- Custom OCR API Helpers ----------
    def _load_custom_ocr_apis(self):
        if not os.path.exists(CUSTOM_OCR_APIS_FILE):
            return {}
        try:
            with open(CUSTOM_OCR_APIS_FILE, "rb") as f:
                payload = pickle.load(f)
        except Exception as e:
            print(f"Custom OCR APIs load error: {e}")
            return {}

        if not isinstance(payload, dict):
            return {}

        apis = {}
        for raw_name, config in payload.items():
            name = str(raw_name).strip() if raw_name is not None else ""
            if not name or not isinstance(config, dict):
                continue
            endpoint = config.get("endpoint")
            if not isinstance(endpoint, str) or not endpoint.strip():
                continue
            headers = config.get("headers", {})
            if headers is None:
                headers = {}
            if not isinstance(headers, dict):
                continue
            apis[name] = {"endpoint": endpoint.strip(), "headers": dict(headers)}
        return apis

    def _save_custom_ocr_apis(self, apis):
        try:
            with open(CUSTOM_OCR_APIS_FILE, "wb") as f:
                pickle.dump(apis, f)
        except Exception as e:
            print(f"Custom OCR APIs save error: {e}")

    def _default_ocr_engine(self) -> str:
        return "RapidOCR" if "RapidOCR" in OCR_ENGINES else (OCR_ENGINES[0] if OCR_ENGINES else "")

    def _refresh_ocr_combo(self, selected=None):
        if not hasattr(self, "combo_ocr"):
            return

        previous = self.combo_ocr.currentText()
        apis = self._load_custom_ocr_apis()

        self.combo_ocr.blockSignals(True)
        self.combo_ocr.clear()
        self.combo_ocr.addItems(OCR_ENGINES)
        for name in sorted(apis.keys()):
            if name not in OCR_ENGINES:
                self.combo_ocr.addItem(name)

        candidates = [selected, previous, self._default_ocr_engine()]
        chosen = ""
        for candidate in candidates:
            if candidate and self.combo_ocr.findText(candidate) >= 0:
                chosen = candidate
                break
        if chosen:
            self.combo_ocr.setCurrentText(chosen)
        self.combo_ocr.blockSignals(False)

        self.worker.ocr_manager.reload_custom_engines()
        if chosen:
            self.worker.set_engine(chosen)

    def open_custom_ocr_api_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(_("Custom OCR APIs"))
        layout = QVBoxLayout(dialog)

        form = QFormLayout()
        name_input = QLineEdit()
        endpoint_input = QLineEdit()
        headers_input = QPlainTextEdit()
        headers_input.setPlaceholderText('{ "Authorization": "Bearer ..." }')
        headers_input.setFixedHeight(90)
        form.addRow(_("OCR Name"), name_input)
        form.addRow(_("API Endpoint"), endpoint_input)
        form.addRow(_("API Header"), headers_input)
        layout.addLayout(form)

        layout.addWidget(QLabel(_("Saved APIs")))
        api_list = QListWidget()
        layout.addWidget(api_list)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        save_button = buttons.addButton(_("Save"), QDialogButtonBox.AcceptRole)
        delete_button = buttons.addButton(_("Delete"), QDialogButtonBox.DestructiveRole)
        layout.addWidget(buttons)

        def refresh_list(selected_name=None):
            api_list.clear()
            apis = self._load_custom_ocr_apis()
            for api_name in sorted(apis.keys()):
                api_list.addItem(api_name)
            if selected_name:
                matches = api_list.findItems(selected_name, Qt.MatchExactly)
                if matches:
                    api_list.setCurrentItem(matches[0])

        def populate_form():
            item = api_list.currentItem()
            if not item:
                return
            apis = self._load_custom_ocr_apis()
            config = apis.get(item.text(), {})
            name_input.setText(item.text())
            endpoint_input.setText(config.get("endpoint", ""))
            headers = config.get("headers", {})
            headers_input.setPlainText(json.dumps(headers, indent=2) if headers else "")

        def builtin_names():
            names = set(OCR_ENGINES)
            names.update(getattr(self.worker.ocr_manager, "builtin_engines", {}).keys())
            return names

        def save_api():
            name = name_input.text().strip()
            endpoint = endpoint_input.text().strip()
            raw_headers = headers_input.toPlainText().strip()

            if not name:
                QMessageBox.warning(dialog, _("Invalid OCR API"), _("OCR Name is required."))
                return
            if not endpoint:
                QMessageBox.warning(dialog, _("Invalid OCR API"), _("API Endpoint is required."))
                return
            if not endpoint.startswith(("http://", "https://")):
                QMessageBox.warning(dialog, _("Invalid OCR API"), _("API Endpoint must start with http:// or https://."))
                return
            if name in builtin_names():
                QMessageBox.warning(dialog, _("Invalid OCR API"), _("Custom OCR API name cannot match a built-in OCR engine."))
                return

            headers = {}
            if raw_headers:
                try:
                    headers = json.loads(raw_headers)
                except Exception as e:
                    QMessageBox.warning(dialog, _("Invalid OCR API"), _("API Header must be a valid JSON object.") + f"\n{e}")
                    return
                if not isinstance(headers, dict):
                    QMessageBox.warning(dialog, _("Invalid OCR API"), _("API Header must be a valid JSON object."))
                    return

            for key in list(headers.keys()):
                if str(key).lower() == "content-type":
                    del headers[key]

            apis = self._load_custom_ocr_apis()
            apis[name] = {"endpoint": endpoint, "headers": headers}
            self._save_custom_ocr_apis(apis)
            refresh_list(name)
            self._refresh_ocr_combo(selected=name)
            self.save_settings()
            print(f"Custom OCR API '{name}' saved.")

        def delete_api():
            item = api_list.currentItem()
            if not item:
                QMessageBox.information(dialog, _("No Selection"), _("Please select a custom OCR API to delete."))
                return
            name = item.text()
            apis = self._load_custom_ocr_apis()
            if name not in apis:
                QMessageBox.warning(dialog, _("Not Found"), _("Custom OCR API not found."))
                refresh_list()
                return

            del apis[name]
            self._save_custom_ocr_apis(apis)
            fallback = self._default_ocr_engine() if self.combo_ocr.currentText() == name else self.combo_ocr.currentText()
            refresh_list()
            name_input.clear()
            endpoint_input.clear()
            headers_input.clear()
            self._refresh_ocr_combo(selected=fallback)
            self.save_settings()
            print(f"Custom OCR API '{name}' deleted.")

        api_list.currentItemChanged.connect(lambda _current, _previous: populate_form())
        save_button.clicked.connect(save_api)
        delete_button.clicked.connect(delete_api)
        buttons.rejected.connect(dialog.reject)

        refresh_list()
        dialog.exec()
 
    # ---------- API Key Helpers ----------
    def _apply_api_key_for_current_engine(self):
        """Update the API key textbox state and value for the current engine."""
        engine = self.combo_translator.currentText()
        key = self.api_keys.get(engine, "")
        # Block signals to avoid triggering on_api_key_changed during load
        self.api_key_input.blockSignals(True)
        self.api_key_input.setText(key)
        self.api_key_input.blockSignals(False)
        # Push to worker so the engine uses the saved key
        if key:
            self.worker.set_api_key(engine, key)
        # Toggle editable state based on engine (always visible, fixed window size)
        self._update_api_key_state(engine)

    def _update_api_key_state(self, engine: str):
        """Enable/disable the API key field based on engine, keep it always visible."""
        engines_needing_key = {"DeepL"}
        if engine in engines_needing_key:
            self.api_key_input.setReadOnly(False)
            self.api_key_input.setEnabled(True)
            self.api_key_input.setToolTip("")
        else:
            self.api_key_input.setReadOnly(True)
            self.api_key_input.setEnabled(False)
            self.api_key_input.setToolTip(_("This engine does not require an API key"))

    def on_translator_changed(self, engine: str):
        """Called when the translation engine combo box changes."""
        self._apply_api_key_for_current_engine()

    def on_api_key_changed(self, text: str):
        """Called when the user types in the API key text box."""
        engine = self.combo_translator.currentText()
        self.api_keys[engine] = text
        self.worker.set_api_key(engine, text)
        self.save_settings()

    # ---------- Preset Management ----------
    def _load_presets_dict(self):
        """Load all presets from pickle file, returns dict."""
        if os.path.exists(PRESETS_FILE):
            try:
                with open(PRESETS_FILE, "rb") as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"Presets load error: {e}")
        return {}

    def _save_presets_dict(self, presets):
        """Save presets dict to pickle file."""
        try:
            with open(PRESETS_FILE, "wb") as f:
                pickle.dump(presets, f)
        except Exception as e:
            print(f"Presets save error: {e}")

    def refresh_preset_list(self):
        """Refresh the combo box with preset names."""
        self.preset_combo.clear()
        presets = self._load_presets_dict()
        for name in sorted(presets.keys()):
            self.preset_combo.addItem(name)

    def save_preset(self):
        """Save current overlay position/size + capture rect + appearance to a named preset."""
        name = self.preset_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "No Name", "Please enter a preset name.")
            return
        
        preset = {
            "capture_rect": (
                self.worker.capture_rect.x(),
                self.worker.capture_rect.y(),
                self.worker.capture_rect.width(),
                self.worker.capture_rect.height(),
            ),
            "overlay_x": self.overlay.pos().x(),
            "overlay_y": self.overlay.pos().y(),
            "overlay_w": self.overlay.width(),
            "overlay_h": self.overlay.height(),
            "font_family": self.overlay.font_family,
            "font_size": self.overlay.font_size,
            "font_color": self.overlay.font_color,
            "bg_color": self.overlay.bg_color,
            "bg_opacity": self.overlay.bg_opacity,
        }
        
        presets = self._load_presets_dict()
        presets[name] = preset
        self._save_presets_dict(presets)
        self.refresh_preset_list()
        self.preset_name_input.clear()
        print(f"Preset '{name}' saved.")

    def load_preset(self):
        """Load the selected preset from the combo box and apply it."""
        name = self.preset_combo.currentText()
        if not name:
            QMessageBox.information(self, _("No Selection"), _("Please select a preset to load."))
            return
        presets = self._load_presets_dict()
        preset = presets.get(name)
        if preset is None:
            QMessageBox.warning(self, "Not Found", f"Preset '{name}' not found.")
            return
        
        # Apply capture rect
        rect_data = preset.get("capture_rect")
        if rect_data:
            self.worker.set_rect(QRect(rect_data[0], rect_data[1], rect_data[2], rect_data[3]))
            self.update_rect_label()
        
        # Apply overlay position and size
        ox = preset.get("overlay_x")
        oy = preset.get("overlay_y")
        ow = preset.get("overlay_w")
        oh = preset.get("overlay_h")
        if ox is not None and oy is not None:
            self.overlay.move(ox, oy)
        if ow is not None and oh is not None:
            self.overlay.resize(ow, oh)
        
        # Apply appearance
        ff = preset.get("font_family")
        if ff:
            self.overlay.set_font_family(ff)
            self.font_picker.setCurrentFont(ff)
        
        fs = preset.get("font_size")
        if fs:
            self.overlay.set_font_size(fs)
            self.font_size_spin.setValue(fs)
        
        fc = preset.get("font_color")
        if fc:
            self.overlay.set_font_color(fc)
            self.color_sample.setStyleSheet(
                f"background-color: {fc}; border: 1px solid gray; border-radius: 4px;"
            )
        
        bgc = preset.get("bg_color")
        if bgc:
            self.overlay.set_bg_color(bgc)
            self.bg_color_sample.setStyleSheet(
                f"background-color: {bgc}; border: 1px solid gray; border-radius: 4px;"
            )
        
        bgo = preset.get("bg_opacity")
        if bgo is not None:
            self.overlay.set_bg_opacity(bgo)
            self.bg_opacity_spin.setValue(bgo)
        
        print(f"Preset '{name}' loaded.")

    def delete_preset(self):
        """Delete the selected preset."""
        name = self.preset_combo.currentText()
        if not name:
            QMessageBox.information(self, "No Selection", "Please select a preset to delete.")
            return
        presets = self._load_presets_dict()
        if name in presets:
            del presets[name]
            self._save_presets_dict(presets)
            self.refresh_preset_list()
            print(f"Preset '{name}' deleted.")
        else:
            QMessageBox.warning(self, "Not Found", f"Preset '{name}' not found.")
