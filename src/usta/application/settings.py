"""Persistent values, independent of Qt and filesystem access."""
from dataclasses import asdict, dataclass, field, fields
import math
from typing import Any

@dataclass
class Preset:
    capture_rect: tuple[int, int, int, int] = (560, 750, 800, 140)
    overlay_x: int = 0
    overlay_y: int = 0
    overlay_w: int = 400
    overlay_h: int = 150
    font_family: str = 'Arial'
    font_size: int = 20
    font_color: str = 'white'
    bg_color: str = '#000000'
    bg_opacity: int = 180
    extra: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        if not isinstance(data, dict):
            raise ValueError('Settings must be an object')
        defaults = cls()
        known = {f.name for f in fields(cls)} - {'extra'}
        values = {}
        for name in known:
            value = data.get(name, getattr(defaults, name))
            default = getattr(defaults, name)
            if name == 'capture_rect':
                valid = isinstance(value, (list, tuple)) and len(value) == 4 and all(type(v) is int for v in value)
                value = tuple(value) if valid and value[2] > 0 and value[3] > 0 else default
            elif name == 'dpi_scale':
                value = float(value) if type(value) in (int, float) and math.isfinite(value) and value > 0 else default
            elif name == 'translator_api_keys':
                value = {k: v for k, v in value.items() if isinstance(k, str) and isinstance(v, str)} if isinstance(value, dict) else {}
            elif type(value) is not type(default):
                value = default
            if name == 'font_size' and value <= 0:
                value = default
            if name == 'bg_opacity' and not 0 <= value <= 255:
                value = default
            values[name] = value
        return cls(**values, extra={k: v for k, v in data.items() if k not in known})

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        extra = data.pop('extra')
        return {**extra, **data}

@dataclass
class AppSettings(Preset):
    ocr_engine: str = 'RapidOCR'
    translator_engine: str = 'Google'
    source_lang: str = 'English'
    target_lang: str = 'Turkish'
    translator_api_keys: dict[str, str] = field(default_factory=dict)
    dpi_scale: float = 1.0
    screenshot_engine: str = 'Portal'
    settings_topmost_hotkey: str = '<shift>+<alt>+m'
    temporary_region_hotkey: str = '<shift>+<alt>+r'
