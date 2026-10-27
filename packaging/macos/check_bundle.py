"""Offline bundle diagnostics: no screen capture, global listeners or network calls."""

import gettext
import io
import json
import logging
import platform
import tempfile
import traceback
from importlib import import_module
from pathlib import Path


def check_bundle(output):
    report = {"ok": False, "architecture": platform.machine()}
    messages = io.StringIO()
    handler = logging.StreamHandler(messages)
    logger = logging.getLogger("usta")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    try:
        import certifi
        import easyocr
        import ScreenCaptureKit
        import torch
        from PIL import Image, ImageDraw, ImageFont
        from PySide6.QtCore import QRect
        from PySide6.QtSvg import QSvgRenderer
        from PySide6.QtWidgets import QApplication

        from usta.application.results import PerformanceTimings
        from usta.config import OS
        from usta.core.ocr.apple_vision_engine import AppleVisionEngine
        from usta.core.ocr.rapidocr_engine import RapidOCREngine
        from usta.core.registry import OCR_FACTORIES, TRANSLATOR_FACTORIES
        from usta.resource_paths import resource_path
        from usta.ui.main_window import ControlPanel
        from usta.ui.tabs.ocr_tab import OCRTab
        from usta.ui.tabs.status_tab import StatusTab

        for module, name in [*OCR_FACTORIES.values(), *TRANSLATOR_FACTORIES.values()]:
            assert getattr(import_module(module), name)
        assert ControlPanel
        assert hasattr(
            ScreenCaptureKit.SCScreenshotManager, "captureImageInRect_completionHandler_"
        )
        assert Path(certifi.where()).is_file()
        assert resource_path("ui/assets/usta.png").is_file()
        assert QSvgRenderer(str(resource_path("ui/assets/select-region.svg"))).isValid()
        translations = resource_path("resources/translations")
        for language in ("tr", "uk"):
            translator = gettext.translation("messages", str(translations), languages=[language])
            assert translator.gettext("Region") != "Region"
        models = list(resource_path("resources/ocr_models/rapidocr").glob("*.onnx"))
        assert len(models) >= 8
        app = QApplication.instance() or QApplication([])
        ocr_tab = OCRTab()
        report["os"] = OS
        report["screen_engines"] = [
            ocr_tab.combo_screenshot.itemText(index)
            for index in range(ocr_tab.combo_screenshot.count())
        ]
        report["ocr_engines"] = [
            ocr_tab.combo_ocr.itemText(index) for index in range(ocr_tab.combo_ocr.count())
        ]
        assert report["os"] == "Darwin", report
        assert report["screen_engines"] == ["MacOS"], report
        assert "Apple Vision" in report["ocr_engines"], report
        ocr_tab.close()
        status = StatusTab()
        status.update_timings(PerformanceTimings(0.32, 1.28, 1.82))
        status.update_region(QRect(-1920, 120, 1280, 720))
        assert status.ocr_value.value() == 0.32
        assert status.region_position.text() == "X -1920   Y 120"
        with tempfile.TemporaryDirectory(prefix="usta-bundle-check-") as directory:
            image_path = Path(directory) / "ocr.png"
            image = Image.new("RGB", (640, 140), "white")
            ImageDraw.Draw(image).text(
                (25, 35), "USTA 12345", fill="black", font=ImageFont.load_default(size=42)
            )
            image.save(image_path)
            for name, engine in (
                ("rapidocr", RapidOCREngine()),
                ("apple_vision", AppleVisionEngine()),
            ):
                text = engine.read_text(str(image_path))
                report[name] = text
                report[f"{name}_error"] = getattr(engine, "_unavailable_reason", None)
                assert "USTA" in text.upper(), f"{name} returned {text!r}"
        report.update(
            ok=True,
            bundled_models=len(models),
            torch=torch.__version__,
            easyocr=easyocr.__version__,
            status_height=status.minimumSizeHint().height(),
        )
        status.close()
        app.processEvents()
    except Exception:
        report["error"] = traceback.format_exc()
    report["log"] = messages.getvalue()
    logger.removeHandler(handler)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if report["ok"] else 1
