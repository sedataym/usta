import unittest
import warnings

from usta.core.ocr.easyocr_engine import EasyOCREngine

PIN_MEMORY_WARNING = (
    "'pin_memory' argument is set as true but not supported on MPS now, "
    "device pinned memory won't be used."
)


class WarningReader:
    """External reader boundary emitting the warnings seen from PyTorch."""

    def __init__(self, device):
        self.device = device

    def readtext(self, image_path):
        warnings.warn_explicit(
            PIN_MEMORY_WARNING,
            UserWarning,
            "dataloader.py",
            759,
            module="torch.utils.data.dataloader",
        )
        warnings.warn_explicit(
            "Other OCR warning",
            UserWarning,
            "dataloader.py",
            760,
            module="torch.utils.data.dataloader",
        )
        return [(None, "  Hello   world: ", 0.95)]


class EasyOCRWarningTests(unittest.TestCase):
    def test_mps_filters_only_known_pin_memory_warning_and_preserves_text(self):
        engine = EasyOCREngine()
        engine.reader = WarningReader("mps")
        with warnings.catch_warnings(record=True) as recorded:
            warnings.simplefilter("always")
            result = engine.read_text("image.png")
        self.assertEqual(result, "Hello world")
        self.assertEqual([str(w.message) for w in recorded], ["Other OCR warning"])
        self.assertEqual(engine.reader.device, "mps")

    def test_cpu_and_cuda_warning_behavior_is_unchanged(self):
        for device in ("cpu", "cuda:0"):
            with self.subTest(device=device):
                engine = EasyOCREngine()
                engine.reader = WarningReader(device)
                with warnings.catch_warnings(record=True) as recorded:
                    warnings.simplefilter("always")
                    engine.read_text("image.png")
                self.assertEqual(
                    [str(w.message) for w in recorded], [PIN_MEMORY_WARNING, "Other OCR warning"]
                )

    def test_warning_filter_is_restored_after_mps_read(self):
        engine = EasyOCREngine()
        engine.reader = WarningReader("mps")
        with warnings.catch_warnings(record=True) as recorded:
            warnings.simplefilter("always")
            engine.read_text("image.png")
            warnings.warn_explicit(
                PIN_MEMORY_WARNING,
                UserWarning,
                "dataloader.py",
                759,
                module="torch.utils.data.dataloader",
            )
        self.assertEqual(
            [str(w.message) for w in recorded], ["Other OCR warning", PIN_MEMORY_WARNING]
        )
