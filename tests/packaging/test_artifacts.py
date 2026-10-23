import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class PackageLayoutTests(unittest.TestCase):
    def test_real_package_and_launchers(self):
        self.assertTrue((ROOT / "src/usta/__main__.py").is_file())
        self.assertNotIn("sys.path.insert", (ROOT / "src/usta/main.py").read_text())
        self.assertIn("usta.main", (ROOT / "run.py").read_text())

    def test_bundled_resources_are_declared(self):
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
        data = tomllib.loads((ROOT / "pyproject.toml").read_text())
        self.assertIn(
            "resources/ocr_models/rapidocr/*.onnx",
            data["tool"]["setuptools"]["package-data"]["usta"],
        )
