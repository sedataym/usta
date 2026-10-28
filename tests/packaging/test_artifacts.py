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

    def test_built_wheel_and_sdist_contain_identical_resources(self):
        import hashlib
        import os
        import tarfile
        import zipfile

        from usta._version import __version__

        wheels = list((ROOT / "dist").glob(f"usta-{__version__}-*.whl"))
        sdists = list((ROOT / "dist").glob(f"usta-{__version__}.tar.gz"))
        if not wheels or not sdists:
            if os.environ.get("USTA_REQUIRE_ARTIFACTS") == "1":
                self.fail("Build artifacts required; run python -m build first")
            self.skipTest("Run python -m build to inspect distribution artifacts")
        with zipfile.ZipFile(wheels[-1]) as wheel, tarfile.open(sdists[-1]) as sdist:
            icon = ROOT / "src/usta/ui/assets/select-region.svg"
            self.assertEqual(wheel.read("usta/ui/assets/select-region.svg"), icon.read_bytes())
            icon_member = next(
                m
                for m in sdist.getmembers()
                if m.name.endswith("/usta/ui/assets/select-region.svg")
            )
            self.assertEqual(sdist.extractfile(icon_member).read(), icon.read_bytes())
            for resource in (ROOT / "src/usta/resources").rglob("*"):
                if not resource.is_file():
                    continue
                suffix = str(resource.relative_to(ROOT / "src"))
                expected = hashlib.sha256(resource.read_bytes()).digest()
                self.assertEqual(hashlib.sha256(wheel.read(suffix)).digest(), expected)
                member = next(m for m in sdist.getmembers() if m.name.endswith("/" + suffix))
                self.assertEqual(
                    hashlib.sha256(sdist.extractfile(member).read()).digest(), expected
                )
