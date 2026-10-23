import json
import os
import pickle
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from usta.application.settings import AppSettings, Preset
from usta.infrastructure.settings_store import SettingsStore


class SettingsStoreTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.store = SettingsStore(self.root)

    def test_roundtrip_and_legacy_migration_preserve_values(self):
        original = {
            "capture_rect": (-300, 20, 400, 60),
            "dpi_scale": 2.0,
            "translator_api_keys": {"DeepL": "private"},
            "font_color": "#abcdef",
        }
        path = self.root / "settings.pkl"
        path.write_bytes(pickle.dumps(original))
        loaded = self.store.load()
        self.assertEqual(loaded.capture_rect, (-300, 20, 400, 60))
        self.assertEqual(loaded.translator_api_keys, original["translator_api_keys"])
        self.assertEqual(loaded.font_color, "#abcdef")
        self.assertEqual(path.read_bytes(), pickle.dumps(original))
        self.assertEqual(self.store.load(), loaded)
        self.assertEqual(os.stat(self.root / "settings.json").st_mode & 0o777, 0o600)

    def test_failed_replace_preserves_previous_settings(self):
        self.store.save(AppSettings(font_size=24))
        with patch("usta.infrastructure.settings_store.os.replace", side_effect=OSError("full")):
            with self.assertRaises(OSError):
                self.store.save(AppSettings(font_size=30))
        self.assertEqual(self.store.load().font_size, 24)
        self.assertEqual(list(self.root.glob("*.tmp")), [])

    def test_future_schema_and_corruption_are_not_overwritten(self):
        path = self.root / "settings.json"
        for raw in ('{"schema_version":99,"data":{}}', "{broken"):
            path.write_text(raw)
            with self.assertRaises(ValueError):
                self.store.load()
            with self.assertRaises(ValueError):
                self.store.save(AppSettings())
            self.assertEqual(path.read_text(), raw)

    def test_legacy_globals_are_rejected_without_execution(self):
        (self.root / "settings.pkl").write_bytes(b'cos\nsystem\n(S"false"\ntR.')
        with self.assertRaises(ValueError):
            self.store.load()
        self.assertFalse((self.root / "settings.json").exists())

    def test_presets_and_missing_fields(self):
        (self.root / "presets.pkl").write_bytes(
            pickle.dumps({"game": {"capture_rect": (-10, 5, 600, 90)}})
        )
        presets = self.store.load_presets()
        self.assertEqual(presets["game"].capture_rect, (-10, 5, 600, 90))
        self.store.save_presets(presets)
        self.assertEqual(self.store.load_presets(), presets)
        self.assertEqual(
            AppSettings.from_dict({"unknown": "retained"}).to_dict()["unknown"], "retained"
        )

    def test_invalid_field_falls_back_without_changing_valid_coordinates(self):
        s = AppSettings.from_dict(
            {"dpi_scale": float("nan"), "font_size": "bad", "capture_rect": [-20, 3, 100, 30]}
        )
        self.assertEqual(s.dpi_scale, 1.0)
        self.assertEqual(s.font_size, 20)
        self.assertEqual(s.capture_rect, (-20, 3, 100, 30))

    def test_malformed_preset_preserves_valid_entries_and_blocks_overwrite(self):
        path = self.root / "presets.json"
        raw = json.dumps(
            {"schema_version": 1, "data": {"valuable": {"font_size": 31}, "broken": None}}
        )
        path.write_text(raw)
        self.assertEqual(self.store.load_presets()["valuable"].font_size, 31)
        with self.assertRaises(ValueError):
            self.store.save_presets({"new": Preset()})
        self.assertEqual(path.read_text(), raw)

    def test_save_without_load_cannot_replace_malformed_presets(self):
        path = self.root / "presets.json"
        raw = json.dumps({"schema_version": 1, "data": {"valuable": {}, "broken": None}})
        path.write_text(raw)
        with self.assertRaises(ValueError):
            self.store.save_presets({"new": Preset()})
        self.assertEqual(path.read_text(), raw)
