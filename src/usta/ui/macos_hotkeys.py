"""Native panel actions for macOS settings and region-selection shortcuts."""
import logging
import os

from usta.ui.macos_overlay import MacOSOverlayRules

logger = logging.getLogger(__name__)


class MacOSHotkeyWindow:
    def __init__(self, widget):
        self.widget = widget
        self.rules = MacOSOverlayRules(widget)
        self._normal_behavior = None
        self._previous_app = None
        try:
            import AppKit
            window = self._window()
            self._normal_behavior = window.collectionBehavior()
            # Prepare before the first show, not after a fullscreen transition.
            if window.isKindOfClass_(AppKit.NSPanel):
                window.setStyleMask_(window.styleMask() | AppKit.NSWindowStyleMaskNonactivatingPanel)
        except Exception as ex:
            logger.error("Could not prepare macOS hotkey panel: %s", ex)

    def _window(self):
        import objc
        return objc.objc_object(c_void_p=int(self.widget.winId())).window()

    def show(self, focus=True):
        # Showing a Qt tool window can change activation before makeKeyWindow.
        # Remember the caller's app before any native window/show operations.
        self._remember_application()
        self.rules.start()
        self.rules.prepare()
        self.widget.show()
        self.rules.order_front_without_activation()
        if focus:
            self.focus()

    def focus(self):
        try:
            self._remember_application()
            # Interactive settings/selection need keyboard input. Unlike Qt's
            # activateWindow/raise path, the panel stays in the fullscreen Space.
            self._window().makeKeyWindow()
        except Exception as ex:
            logger.error("Could not focus macOS hotkey panel: %s", ex)

    def _remember_application(self):
        try:
            import AppKit
            previous = AppKit.NSWorkspace.sharedWorkspace().frontmostApplication()
            if previous is not None and previous.processIdentifier() != os.getpid():
                self._previous_app = previous
        except Exception as ex:
            logger.error("Could not remember application for macOS hotkey action: %s", ex)

    def lower(self):
        self.rules.stop()
        try:
            import AppKit
            window = self._window()
            window.resignKeyWindow()
            if self._normal_behavior is not None:
                window.setCollectionBehavior_(self._normal_behavior)
            window.setLevel_(AppKit.NSNormalWindowLevel)
            window.orderBack_(None)
        except Exception as ex:
            logger.error("Could not lower macOS hotkey panel: %s", ex)
        self._restore_focus()

    def _restore_focus(self):
        previous, self._previous_app = self._previous_app, None
        if previous is None:
            return
        try:
            import AppKit
            current = AppKit.NSWorkspace.sharedWorkspace().frontmostApplication()
            if current is not None and current.processIdentifier() == os.getpid() and not previous.isTerminated():
                # macOS 14+ uses cooperative activation; the old ignore-other-
                # apps flag no longer guarantees handing focus back.
                if hasattr(AppKit.NSApp, "yieldActivationToApplication_"):
                    AppKit.NSApp.yieldActivationToApplication_(previous)
                    previous.activateFromApplication_options_(
                        AppKit.NSRunningApplication.currentApplication(), 0,
                    )
                else:
                    previous.activateWithOptions_(AppKit.NSApplicationActivateIgnoringOtherApps)
        except Exception as ex:
            logger.error("Could not restore focus after macOS hotkey action: %s", ex)

    def stop(self):
        self.rules.stop()
        self._restore_focus()
