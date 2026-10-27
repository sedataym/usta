"""Read-only privacy preflight, launched through Finder/Launch Services."""

import json
import os
import sys
from pathlib import Path


def check_permissions(output: Path):
    import ApplicationServices
    import Foundation
    import Quartz
    from PySide6.QtWidgets import QApplication

    from usta._version import __version__

    app = QApplication.instance() or QApplication(sys.argv[:1])
    bundle = Foundation.NSBundle.mainBundle()
    report = {
        "version": __version__,
        "bundle_id": str(bundle.bundleIdentifier()),
        "bundle_path": str(bundle.bundlePath()),
        "executable": sys.executable,
        "pid": os.getpid(),
        "screen_recording": bool(Quartz.CGPreflightScreenCaptureAccess()),
        "accessibility": bool(ApplicationServices.AXIsProcessTrusted()),
        "input_monitoring": bool(Quartz.CGPreflightListenEventAccess()),
    }
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    del app
    return 0
