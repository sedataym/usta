"""Keep a Qt overlay's Cocoa rules in sync with macOS window transitions."""
import weakref

from PySide6.QtCore import QEvent, QObject, QTimer


def _remove_observers(observers):
    for center, token in observers:
        center.removeObserver_(token)
    observers.clear()


class MacOSOverlayRules(QObject):
    def __init__(self, widget):
        super().__init__(widget)
        self._widget = widget
        self._observers = []
        self._running = False
        self._immediate = QTimer(self)
        self._settled = QTimer(self)
        for timer in (self._immediate, self._settled):
            timer.setSingleShot(True)
            timer.timeout.connect(self._apply)
        widget.installEventFilter(self)
        # The cleanup closure must not retain this QObject or the widget.
        observers = self._observers
        self.destroyed.connect(lambda: _remove_observers(observers))

    def start(self):
        if self._running:
            self._schedule()
            return
        try:
            import AppKit

            reference = weakref.ref(self)

            def changed(_notification):
                rules = reference()
                if rules is not None:
                    rules._schedule()

            workspace = AppKit.NSWorkspace.sharedWorkspace().notificationCenter()
            local = AppKit.NSNotificationCenter.defaultCenter()
            notifications = (
                (workspace, AppKit.NSWorkspaceActiveSpaceDidChangeNotification),
                (workspace, AppKit.NSWorkspaceDidActivateApplicationNotification),
                (local, AppKit.NSWindowDidEnterFullScreenNotification),
                (local, AppKit.NSWindowDidExitFullScreenNotification),
            )
            for center, name in notifications:
                token = center.addObserverForName_object_queue_usingBlock_(
                    name, None, AppKit.NSOperationQueue.mainQueue(), changed,
                )
                self._observers.append((center, token))
            self._running = True
            self._schedule()
        except Exception as ex:
            _remove_observers(self._observers)
            print(f"macOS overlay bildirimleri başlatılamadı: {ex}")

    def stop(self):
        self._running = False
        self._immediate.stop()
        self._settled.stop()
        _remove_observers(self._observers)

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Show, QEvent.WinIdChange, QEvent.WindowStateChange):
            self._schedule()
        return super().eventFilter(watched, event)

    def _schedule(self):
        if self._running:
            self._immediate.start(0)
            # Qt/Cocoa may update native flags later in the transition.
            self._settled.start(350)

    def order_front_without_activation(self):
        if not self._widget.isVisible():
            return
        try:
            import objc

            view = objc.objc_object(c_void_p=int(self._widget.winId()))
            window = view.window()
            if window is not None:
                # Qt.raise_ also activates NSApp, stealing fullscreen focus.
                window.orderFrontRegardless()
        except Exception as ex:
            print(f"macOS overlay öne getirilemedi: {ex}")

    def prepare(self):
        """Configure a panel before ordering it into an existing fullscreen Space."""
        self._apply(allow_hidden=True)

    def _apply(self, allow_hidden=False):
        if not self._running or (not allow_hidden and not self._widget.isVisible()):
            return
        try:
            import AppKit
            import objc

            # Qt's macOS winId is an NSView; resolve its current owning window.
            view = objc.objc_object(c_void_p=int(self._widget.winId()))
            window = view.window()
            if window is None:
                return
            # Qt.Tool creates an NSPanel, but WindowDoesNotAcceptFocus does not
            # give it Cocoa's nonactivating style. Without that style the panel
            # remains on the desktop when another app enters a fullscreen Space.
            if window.isKindOfClass_(AppKit.NSPanel):
                style = window.styleMask() | AppKit.NSWindowStyleMaskNonactivatingPanel
                if style != window.styleMask():
                    window.setStyleMask_(style)
            behavior = (AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces |
                        AppKit.NSWindowCollectionBehaviorFullScreenAuxiliary |
                        AppKit.NSWindowCollectionBehaviorStationary)
            # Older macOS/PyObjC versions may not expose this behavior.
            behavior |= getattr(AppKit, "NSWindowCollectionBehaviorCanJoinAllApplications", 0)
            # Build the mask explicitly: primary/auxiliary conflict with joining all apps.
            window.setCollectionBehavior_(behavior)
            window.setLevel_(AppKit.NSStatusWindowLevel)
            window.setHidesOnDeactivate_(False)
        except Exception as ex:
            print(f"macOS pencere kuralları uygulanamadı: {ex}")
