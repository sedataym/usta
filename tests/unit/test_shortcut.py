import contextlib
import os
import sys
import threading
import unittest
from unittest import mock

from usta.core.shortcut import GlobalHotkey, keyboard


class PlatformHotkeyTests(unittest.TestCase):
    def test_linux_and_windows_keep_the_existing_pynput_listener(self):
        for platform in ("linux", "win32"):
            with self.subTest(platform=platform):
                backend = mock.Mock()
                backend.HotKey.parse.return_value = {"ctrl", "x"}
                with (
                    mock.patch("usta.core.shortcut.sys.platform", platform),
                    mock.patch("usta.core.shortcut.keyboard", backend),
                    mock.patch.dict(
                        sys.modules,
                        {
                            "usta.core.platform.macos.hotkey_listener": None,
                        },
                    ),
                ):
                    hotkey = GlobalHotkey("<ctrl>+x", lambda: None)
                    self.assertTrue(hotkey.start())
                    backend.Listener.assert_called_once_with(
                        on_press=hotkey._on_press,
                        on_release=hotkey._on_release,
                    )
                    listener = backend.Listener.return_value
                    listener.start.assert_called_once()
                    hotkey.stop()
                    listener.stop.assert_called_once()


@unittest.skipUnless(
    os.environ.get("USTA_NATIVE_TESTS") == "1"
    and sys.platform == "darwin"
    and keyboard is not None,
    "Requires macOS pynput backend",
)
class MacOSHotkeyThreadTests(unittest.TestCase):
    def test_rebinding_reads_keyboard_layout_on_main_thread_only(self):
        layout_threads = []
        listener_threads = []
        contexts = []

        @contextlib.contextmanager
        def keyboard_layout():
            layout_threads.append(threading.current_thread())
            yield (40, b"copied keyboard layout")

        def listen(listener):
            listener_threads.append(threading.current_thread())
            contexts.append(listener._context)
            listener._mark_ready()

        # Substitute OS calls, leaving actual listener construction/threading intact.
        with (
            mock.patch("pynput.keyboard._darwin.keycode_context", keyboard_layout),
            mock.patch("pynput._util.darwin.keycode_context", keyboard_layout),
            mock.patch("pynput._util.darwin.ListenerMixin._run", listen),
            mock.patch(
                "usta.core.platform.macos.hotkey_listener.has_accessibility_permission",
                return_value=True,
            ),
        ):
            for combination in ("<shift>+<alt>+m", "<ctrl>+<alt>+x", "<cmd>+<shift>+k"):
                hotkey = GlobalHotkey(combination, lambda: None)
                self.assertTrue(hotkey.start())
                hotkey._listener.join(timeout=2)
                hotkey.stop()
        self.assertEqual(layout_threads, [threading.main_thread()] * 3)
        self.assertEqual(len(listener_threads), 3)
        self.assertTrue(all(thread is not threading.main_thread() for thread in listener_threads))
        self.assertEqual(contexts, [(40, b"copied keyboard layout")] * 3)

    def test_off_main_thread_registration_fails_safely(self):
        result = []
        hotkey = GlobalHotkey("<ctrl>+x", lambda: None)
        with mock.patch("pynput._util.darwin.keycode_context") as layout:
            with self.assertLogs("usta.core.shortcut", level="ERROR"):
                thread = threading.Thread(target=lambda: result.append(hotkey.start()))
                thread.start()
                thread.join(timeout=2)
            layout.assert_not_called()
        self.assertEqual(result, [False])
        self.assertIsNone(hotkey._listener)


class MacOSPermissionTests(unittest.TestCase):
    def test_missing_accessibility_warns_once_without_blocking_event_taps(self):
        import types

        import usta.core.shortcut as shortcut

        module = types.ModuleType("usta.core.platform.macos.hotkey_listener")
        module.MainThreadLayoutListener = mock.Mock()
        module.has_accessibility_permission = mock.Mock(return_value=False)
        with (
            mock.patch.object(shortcut.sys, "platform", "darwin"),
            mock.patch.object(
                shortcut,
                "keyboard",
                mock.Mock(HotKey=mock.Mock(parse=mock.Mock(return_value={"ctrl", "x"}))),
            ),
            mock.patch.object(shortcut, "_permission_warning_emitted", False, create=True),
            mock.patch.dict(sys.modules, {"usta.core.platform.macos.hotkey_listener": module}),
        ):
            with self.assertLogs("usta.core.shortcut", level="WARNING") as logs:
                self.assertTrue(GlobalHotkey("<ctrl>+x", lambda: None).start())
                self.assertTrue(GlobalHotkey("<ctrl>+y", lambda: None).start())
            self.assertEqual(len(logs.output), 1)
            self.assertIn("Accessibility", logs.output[0])
            self.assertEqual(module.MainThreadLayoutListener.call_count, 2)

    def test_new_listener_rechecks_permission_after_grant(self):
        import types

        import usta.core.shortcut as shortcut

        module = types.ModuleType("usta.core.platform.macos.hotkey_listener")
        module.MainThreadLayoutListener = mock.Mock()
        module.has_accessibility_permission = mock.Mock(side_effect=[False, True])
        with (
            mock.patch.object(shortcut.sys, "platform", "darwin"),
            mock.patch.object(
                shortcut,
                "keyboard",
                mock.Mock(HotKey=mock.Mock(parse=mock.Mock(return_value={"ctrl", "x"}))),
            ),
            mock.patch.object(shortcut, "_permission_warning_emitted", True, create=True),
            mock.patch.dict(sys.modules, {"usta.core.platform.macos.hotkey_listener": module}),
        ):
            hotkey = GlobalHotkey("<ctrl>+x", lambda: None)
            self.assertTrue(hotkey.start())
            hotkey.stop()
            self.assertTrue(hotkey.start())
            self.assertEqual(module.MainThreadLayoutListener.return_value.start.call_count, 2)
            hotkey.stop()
