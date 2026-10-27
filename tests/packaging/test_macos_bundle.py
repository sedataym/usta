"""Opt-in acceptance check against the frozen application, not the source environment."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


@unittest.skipUnless(
    sys.platform == "darwin" and os.environ.get("USTA_REQUIRE_MACOS_APP") == "1",
    "Requires an explicitly selected macOS application build",
)
class MacOSBundleTests(unittest.TestCase):
    def test_frozen_ocr_tab_exposes_native_macos_engines(self):
        default_app = Path(__file__).resolve().parents[2] / "dist/macos/USTA.app"
        app = Path(os.environ.get("USTA_MACOS_APP", str(default_app)))
        with tempfile.TemporaryDirectory(prefix="usta-macos-test-") as directory:
            output = Path(directory) / "report.json"
            process = subprocess.run(
                [str(app / "Contents/MacOS/USTA"), "--check-bundle", str(output)],
                capture_output=True,
                text=True,
                timeout=90,
            )
            self.assertTrue(output.is_file(), process.stderr)
            report = json.loads(output.read_text())
            self.assertEqual(process.returncode, 0, report.get("error", process.stderr))
            self.assertEqual(report.get("os"), "Darwin")
            self.assertEqual(report.get("screen_engines"), ["MacOS"])
            self.assertIn("Apple Vision", report.get("ocr_engines", []))
