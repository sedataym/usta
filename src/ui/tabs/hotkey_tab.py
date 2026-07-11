from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from src.i18n import _


HOTKEY_BUTTON_WIDTH = 120
RESET_BUTTON_WIDTH = 60


class HotkeyCaptureButton(QPushButton):
    hotkeyChanged = Signal(str)

    _MODIFIER_ORDER = (
        (Qt.KeyboardModifier.ShiftModifier, "<shift>"),
        (Qt.KeyboardModifier.ControlModifier, "<ctrl>"),
        (Qt.KeyboardModifier.AltModifier, "<alt>"),
        (Qt.KeyboardModifier.MetaModifier, "<cmd>"),
    )

    _IGNORED_KEYS = {
        Qt.Key.Key_Control,
        Qt.Key.Key_Alt,
        Qt.Key.Key_Shift,
        Qt.Key.Key_Meta,
        Qt.Key.Key_AltGr,
        Qt.Key.Key_unknown,
    }

    _SPECIAL_KEYS = {
        Qt.Key.Key_Escape: "<esc>",
        Qt.Key.Key_Tab: "<tab>",
        Qt.Key.Key_Backtab: "<tab>",
        Qt.Key.Key_Backspace: "<backspace>",
        Qt.Key.Key_Return: "<enter>",
        Qt.Key.Key_Enter: "<enter>",
        Qt.Key.Key_Space: "<space>",
        Qt.Key.Key_Delete: "<delete>",
        Qt.Key.Key_Insert: "<insert>",
        Qt.Key.Key_Home: "<home>",
        Qt.Key.Key_End: "<end>",
        Qt.Key.Key_PageUp: "<page_up>",
        Qt.Key.Key_PageDown: "<page_down>",
        Qt.Key.Key_Left: "<left>",
        Qt.Key.Key_Right: "<right>",
        Qt.Key.Key_Up: "<up>",
        Qt.Key.Key_Down: "<down>",
    }

    def __init__(self, hotkey, parent=None):
        super().__init__(parent)
        self._hotkey = hotkey
        self._capturing = False
        self.setFixedWidth(HOTKEY_BUTTON_WIDTH)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(self.start_capture)
        self._refresh_text()

    def hotkey(self):
        return self._hotkey

    def set_hotkey(self, hotkey):
        self._hotkey = hotkey
        self._capturing = False
        self._refresh_text()

    def start_capture(self):
        self._capturing = True
        self.setFocus()
        self.setText(_("Press shortcut..."))

    def focusOutEvent(self, event):
        if self._capturing:
            self._capturing = False
            self._refresh_text()
        super().focusOutEvent(event)

    def keyPressEvent(self, event):
        if not self._capturing:
            super().keyPressEvent(event)
            return

        key = event.key()
        if key == Qt.Key.Key_Escape:
            self._capturing = False
            self._refresh_text()
            event.accept()
            return

        if key in self._IGNORED_KEYS:
            event.accept()
            return

        hotkey = self._event_to_hotkey(event)
        if hotkey:
            self._capturing = False
            self.set_hotkey(hotkey)
            self.hotkeyChanged.emit(hotkey)

        event.accept()

    def _event_to_hotkey(self, event):
        parts = [token for modifier, token in self._MODIFIER_ORDER if event.modifiers() & modifier]
        key_token = self._key_to_token(event)
        if not key_token:
            return ""
        parts.append(key_token)
        return "+".join(parts)

    def _key_to_token(self, event):
        key = event.key()
        if key in self._SPECIAL_KEYS:
            return self._SPECIAL_KEYS[key]

        if Qt.Key.Key_F1 <= key <= Qt.Key.Key_F35:
            return f"<f{key - Qt.Key.Key_F1 + 1}>"

        text = event.text().strip().lower()
        if len(text) == 1 and text.isprintable():
            return text

        sequence = QKeySequence(key).toString(QKeySequence.SequenceFormat.PortableText).lower()
        if len(sequence) == 1 and sequence.isprintable():
            return sequence
        return ""

    def _refresh_text(self):
        self.setText(self._hotkey or _("Click to set shortcut"))


def _add_hotkey_row(layout, label_text, button, reset_callback, tooltip):
    row = QHBoxLayout()
    label = QLabel(label_text)
    label.setToolTip(tooltip)
    button.setToolTip(tooltip)
    row.addWidget(label)
    row.addWidget(button)
    reset_button = QPushButton(_("Reset"))
    reset_button.setFixedWidth(RESET_BUTTON_WIDTH)
    reset_button.setToolTip(tooltip)
    reset_button.clicked.connect(reset_callback)
    row.addWidget(reset_button)
    layout.addLayout(row)


def build_hotkey_tab(panel):
    tab_settings = QWidget()
    tab_settings_layout = QVBoxLayout(tab_settings)
    tab_settings_layout.addWidget(QLabel(_("<b>Hotkeys</b>")))

    settings_topmost_tooltip = _(
        "Use this shortcut to bring the main window to the front while playing a game or watching a video."
    )
    temporary_region_tooltip = _(
        "Use this shortcut when you want to select an area outside your current selection. "
        "The temporary area you select will be active for 10 seconds."
    )

    panel.settings_topmost_hotkey_button = HotkeyCaptureButton(panel.settings_topmost_hotkey)
    panel.settings_topmost_hotkey_button.hotkeyChanged.connect(panel.on_settings_topmost_hotkey_changed)
    _add_hotkey_row(
        tab_settings_layout,
        _("Settings topmost key:"),
        panel.settings_topmost_hotkey_button,
        panel.reset_settings_topmost_hotkey,
        settings_topmost_tooltip,
    )

    panel.temporary_region_hotkey_button = HotkeyCaptureButton(panel.temporary_region_hotkey)
    panel.temporary_region_hotkey_button.hotkeyChanged.connect(panel.on_temporary_region_hotkey_changed)
    _add_hotkey_row(
        tab_settings_layout,
        _("Temporary region key:"),
        panel.temporary_region_hotkey_button,
        panel.reset_temporary_region_hotkey,
        temporary_region_tooltip,
    )

    hint = QLabel(_("Click a shortcut field, then press the key combination you want to use."))
    hint.setWordWrap(True)
    tab_settings_layout.addWidget(hint)
    tab_settings_layout.addStretch()
    return tab_settings
