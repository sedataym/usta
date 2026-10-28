import unittest
from pathlib import Path

from usta.infrastructure.paths import CaptureWorkspace


class RuntimePathTests(unittest.TestCase):
    def test_capture_workspaces_are_private_and_independent(self):
        first, second = CaptureWorkspace(), CaptureWorkspace()
        self.addCleanup(first.close)
        self.addCleanup(second.close)
        self.assertNotEqual(first.image_path, second.image_path)
        Path(first.image_path).write_text("frame")
        first.close()
        self.assertFalse(Path(first.image_path).exists())
        self.assertTrue(Path(second.image_path).parent.is_dir())
