from __future__ import annotations

import logging
from typing import Callable

try:
    from pynput import keyboard
except ImportError:  # pragma: no cover - depends on optional runtime dependency
    keyboard = None

logger = logging.getLogger(__name__)


class GlobalHotkey:
    """Small wrapper around pynput's global hotkey listener."""

    def __init__(self, hotkey: str, callback: Callable[[], None]):
        self.hotkey = hotkey
        self.callback = callback
        self._listener = None
        self._hotkey = None
        self._hotkey_keys = frozenset()
        self._is_pressed = False

    def _on_activate(self):
        if self._is_pressed:
            return

        self._is_pressed = True
        self.callback()

    def _on_press(self, key):
        self._hotkey.press(self._listener.canonical(key))

    def _on_release(self, key):
        canonical_key = self._listener.canonical(key)
        self._hotkey.release(canonical_key)
        if canonical_key in self._hotkey_keys:
            self._is_pressed = False

    def start(self) -> bool:
        if keyboard is None:
            logger.warning("Global hotkey support is unavailable because pynput is not installed.")
            return False

        if self._listener is not None:
            return True

        try:
            hotkey_keys = keyboard.HotKey.parse(self.hotkey)
            self._hotkey_keys = frozenset(hotkey_keys)
            self._hotkey = keyboard.HotKey(hotkey_keys, self._on_activate)
            self._listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release,
            )
            self._listener.start()
        except Exception:
            logger.exception("Failed to start global hotkey listener for %s", self.hotkey)
            self._listener = None
            self._hotkey = None
            self._hotkey_keys = frozenset()
            self._is_pressed = False
            return False

        return True

    def stop(self):
        if self._listener is None:
            return

        try:
            self._listener.stop()
        except Exception:
            logger.exception("Failed to stop global hotkey listener for %s", self.hotkey)
        finally:
            self._listener = None
            self._hotkey = None
            self._hotkey_keys = frozenset()
            self._is_pressed = False
