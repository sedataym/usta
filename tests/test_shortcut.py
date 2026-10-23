import contextlib
import sys
import threading
import unittest
from unittest import mock

from src.core.shortcut import GlobalHotkey, keyboard


class PlatformHotkeyTests(unittest.TestCase):
    def test_linux_and_windows_keep_the_existing_pynput_listener(self):
        for platform in ('linux', 'win32'):
            with self.subTest(platform=platform):
                backend = mock.Mock()
                backend.HotKey.parse.return_value = {'ctrl', 'x'}
                with mock.patch('src.core.shortcut.sys.platform', platform), \
                     mock.patch('src.core.shortcut.keyboard', backend), \
                     mock.patch.dict(sys.modules, {
                         'src.core.platform.macos.hotkey_listener': None,
                     }):
                    hotkey = GlobalHotkey('<ctrl>+x', lambda: None)
                    self.assertTrue(hotkey.start())
                    backend.Listener.assert_called_once_with(
                        on_press=hotkey._on_press, on_release=hotkey._on_release,
                    )
                    listener = backend.Listener.return_value
                    listener.start.assert_called_once()
                    hotkey.stop()
                    listener.stop.assert_called_once()


@unittest.skipUnless(sys.platform == 'darwin' and keyboard is not None,
                     'Requires macOS pynput backend')
class MacOSHotkeyThreadTests(unittest.TestCase):
    def test_rebinding_reads_keyboard_layout_on_main_thread_only(self):
        layout_threads = []
        listener_threads = []
        contexts = []

        @contextlib.contextmanager
        def keyboard_layout():
            layout_threads.append(threading.current_thread())
            yield (40, b'copied keyboard layout')

        def listen(listener):
            listener_threads.append(threading.current_thread())
            contexts.append(listener._context)
            listener._mark_ready()

        # Substitute OS calls, leaving actual listener construction/threading intact.
        with mock.patch('pynput.keyboard._darwin.keycode_context', keyboard_layout), \
             mock.patch('pynput._util.darwin.keycode_context', keyboard_layout), \
             mock.patch('pynput._util.darwin.ListenerMixin._run', listen):
            for combination in ('<shift>+<alt>+m', '<ctrl>+<alt>+x', '<cmd>+<shift>+k'):
                hotkey = GlobalHotkey(combination, lambda: None)
                self.assertTrue(hotkey.start())
                hotkey._listener.join(timeout=2)
                hotkey.stop()
        self.assertEqual(layout_threads, [threading.main_thread()] * 3)
        self.assertEqual(len(listener_threads), 3)
        self.assertTrue(all(thread is not threading.main_thread() for thread in listener_threads))
        self.assertEqual(contexts, [(40, b'copied keyboard layout')] * 3)

    def test_off_main_thread_registration_fails_safely(self):
        result = []
        hotkey = GlobalHotkey('<ctrl>+x', lambda: None)
        with mock.patch('pynput._util.darwin.keycode_context') as layout:
            with self.assertLogs('src.core.shortcut', level='ERROR'):
                thread = threading.Thread(target=lambda: result.append(hotkey.start()))
                thread.start()
                thread.join(timeout=2)
            layout.assert_not_called()
        self.assertEqual(result, [False])
        self.assertIsNone(hotkey._listener)
