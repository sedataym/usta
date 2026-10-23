"""Replace hotkey listeners only after the candidate registered successfully."""
from usta.core.shortcut import GlobalHotkey

class HotkeyController:
    def __init__(self, initial, callback):
        self.hotkey = initial
        self.callback = callback
        self.listener = GlobalHotkey(initial, callback)
        self.listener.start()

    def set_hotkey(self, hotkey):
        if hotkey == self.hotkey:
            return True
        candidate = GlobalHotkey(hotkey, self.callback)
        if not candidate.start():
            return False
        self.listener.stop()
        self.listener = candidate
        self.hotkey = hotkey
        return True

    def close(self):
        self.listener.stop()
