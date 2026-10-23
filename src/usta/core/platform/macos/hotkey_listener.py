"""Keep macOS keyboard-layout queries off pynput's listener thread."""

import threading

from pynput import keyboard
from pynput._util import darwin


class MainThreadLayoutListener(keyboard.Listener):
    def __init__(self, *args, **kwargs):
        if threading.current_thread() is not threading.main_thread():
            raise RuntimeError("macOS hotkey listeners must be created on the main thread")
        super().__init__(*args, **kwargs)
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
