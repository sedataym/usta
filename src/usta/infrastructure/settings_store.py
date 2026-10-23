"""Versioned, atomic settings storage with non-destructive legacy migration."""
import json
import os
import tempfile
from pathlib import Path
from usta.application.settings import AppSettings, Preset
from usta.infrastructure.legacy_settings import load_legacy

class SettingsStore:
    def __init__(self, directory: Path):
        self.directory = Path(directory)
        self._blocked: set[str] = set()

    def _read(self, name: str) -> dict:
        path = self.directory / f'{name}.json'
        try:
            if path.exists():
                content = json.loads(path.read_text(encoding='utf-8'))
                if not isinstance(content, dict) or content.get('schema_version') != 1 or not isinstance(content.get('data'), dict):
                    raise ValueError('Unsupported settings format; original file preserved')
                self._blocked.discard(name)
                return content['data']
            legacy = self.directory / f'{name}.pkl'
            return load_legacy(legacy) if legacy.exists() else {}
        except (ValueError, OSError):
            self._blocked.add(name)
            raise

    def _write(self, name: str, data: dict) -> None:
        if name in self._blocked:
            raise ValueError('Cannot overwrite unreadable settings; original file preserved')
        # Validate existing JSON even when save was called before load.
        path = self.directory / f'{name}.json'
        if path.exists():
            self._read(name)
        self.directory.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(suffix='.tmp', dir=self.directory)
        try:
            with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
                json.dump({'schema_version': 1, 'data': data}, stream, ensure_ascii=False, allow_nan=False)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def load(self) -> AppSettings:
        settings = AppSettings.from_dict(self._read('settings'))
        if not (self.directory / 'settings.json').exists() and (self.directory / 'settings.pkl').exists():
            self.save(settings)
            return AppSettings.from_dict(self._read('settings'))
        return settings

    def save(self, settings: AppSettings) -> None:
        self._write('settings', settings.to_dict())

    def load_presets(self) -> dict[str, Preset]:
        presets = {name: Preset.from_dict(value) for name, value in self._read('presets').items()}
        if not (self.directory / 'presets.json').exists() and (self.directory / 'presets.pkl').exists():
            self.save_presets(presets)
            return {name: Preset.from_dict(value) for name, value in self._read('presets').items()}
        return presets

    def save_presets(self, presets: dict[str, Preset]) -> None:
        self._write('presets', {name: value.to_dict() for name, value in presets.items()})
