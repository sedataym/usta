import unittest
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[2]


class MetadataTests(unittest.TestCase):
    def test_runtime_dependencies_are_complete(self):
        data = tomllib.loads((ROOT / "pyproject.toml").read_text())
        deps = data["project"]["dependencies"]
        self.assertTrue(any(d.startswith("deepl>=") for d in deps))
        self.assertTrue(any(d.startswith("pynput>=") for d in deps))
        self.assertFalse(any(d.startswith("paddleocr") for d in deps))
        self.assertIn("paddle", data["project"]["optional-dependencies"])
        self.assertEqual((ROOT / "requirements.txt").read_text().strip(), ".")
