"""Keep macOS keyboard-layout queries off pynput's listener thread."""

import logging
import threading

from pynput import keyboard
from pynput._util import darwin


def has_accessibility_permission() -> bool:
    """Inspect trust without opening a prompt or changing macOS permissions."""
    if threading.current_thread() is not threading.main_thread():
        raise RuntimeError("macOS hotkey listeners must be created on the main thread")
    return bool(darwin.HIServices.AXIsProcessTrusted())


class _ShortcutLogAdapter(logging.LoggerAdapter):
    def log(self, level, message, *args, **kwargs):
        # GlobalHotkey already reports this permission state once with guidance.
        # Preserve event-tap startup: input-monitoring permission can be separate.
        if level == logging.WARNING and str(message).startswith("This process is not trusted!"):
            return
        super().log(level, message, *args, **kwargs)


class MainThreadLayoutListener(keyboard.Listener):
    def __init__(self, *args, **kwargs):
        if threading.current_thread() is not threading.main_thread():
            raise RuntimeError("macOS hotkey listeners must be created on the main thread")
        super().__init__(*args, **kwargs)
        self._log = _ShortcutLogAdapter(self._log, {})
        # macOS 26 requires the TIS/TSM layout query on the main thread. The
        # context contains copied layout bytes, safe to use on the listener thread.
        with darwin.keycode_context() as context:
            self._layout_context = context

    def _run(self):
        self._context = self._layout_context
        try:
            # Skip keyboard.Listener._run(), which queries TIS from this thread.
            # Keep pynput's existing event tap, callbacks, and shutdown behavior.
            darwin.ListenerMixin._run(self)
        finally:
            self._context = None
