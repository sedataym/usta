import unittest
from unittest.mock import patch, Mock
from usta.core.translation.deepl_engine import DeepLTranslatorEngine
from usta.core.ocr.ocr_manager import OCRManager
from usta.application.results import EngineError

class EngineContracts(unittest.TestCase):
    def test_missing_key_is_error_not_translation(self):
        with self.assertRaises(EngineError): DeepLTranslatorEngine(api_key='').translate('hello')

    def test_manager_constructs_only_selected_engine_and_applies_language(self):
        manager = OCRManager()
        manager.set_language('ko')
        self.assertEqual(manager.engines.instances, {})
        manager.set_engine('EasyOCR')
        self.assertEqual(manager.engines.instances, {})
        reader = manager.engines['EasyOCR']
        self.assertIn('ko', reader.current_langs)
        self.assertEqual(set(manager.engines.instances), {'EasyOCR'})

    def test_capture_close_is_idempotent(self):
        from usta.core.screenshot.spectacle_screenshot import SpectacleScreenshot
        engine=SpectacleScreenshot()
        engine.close();engine.close()

    def test_deepl_client_uses_supported_constructor(self):
        engine = DeepLTranslatorEngine(api_key='test-key')
        self.assertIsNotNone(engine.translator)
        engine.translator.close()
