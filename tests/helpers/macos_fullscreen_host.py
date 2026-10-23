"""Separate, focused app for testing native macOS fullscreen Spaces."""
import json
from pathlib import Path
import sys

import AppKit
import objc
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QLabel


app = QApplication([])
state_file = Path(sys.argv[1])
exit_file = Path(sys.argv[2])
widget = QLabel("USTA fullscreen integration test — closes automatically")
widget.setStyleSheet("background: #224488; color: white; font-size: 24px")
widget.setGeometry(100, 100, 900, 600)
widget.show()
window = objc.objc_object(c_void_p=int(widget.winId())).window()
center = AppKit.NSNotificationCenter.defaultCenter()


def report(_notification):
    state_file.write_text(json.dumps({
        "fullscreen": bool(window.styleMask() & AppKit.NSWindowStyleMaskFullScreen),
        "active": bool(AppKit.NSApp.isActive()),
    }))


tokens = [center.addObserverForName_object_queue_usingBlock_(
    name, window, None, report,
) for name in (AppKit.NSWindowDidEnterFullScreenNotification,
               AppKit.NSWindowDidExitFullScreenNotification)]


def enter_fullscreen():
    window.setCollectionBehavior_(AppKit.NSWindowCollectionBehaviorFullScreenPrimary)
    window.makeKeyAndOrderFront_(None)
    AppKit.NSApp.activateIgnoringOtherApps_(True)
    # The same native transition invoked by the green titlebar button.
    window.toggleFullScreen_(None)


def check_exit_request():
    if exit_file.exists():
        exit_timer.stop()
        window.toggleFullScreen_(None)


exit_timer = QTimer()
exit_timer.timeout.connect(check_exit_request)
exit_timer.start(100)
QTimer.singleShot(500, enter_fullscreen)
QTimer.singleShot(20000, app.quit)
app.exec()
for token in tokens:
    center.removeObserver_(token)
