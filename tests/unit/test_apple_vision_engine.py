import os
import importlib.util
from pathlib import Path
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
import unittest
from unittest import mock

from PIL import Image, ImageDraw, ImageFont

from usta.core.ocr.apple_vision_engine import AppleVisionEngine
from usta.core.ocr.ocr_manager import OCRManager
from usta.core.platform.capability_resolver import resolve_capabilities


class VisionRegistrationTests(unittest.TestCase):
    def test_missing_vision_dependency_is_reported_once_without_crashing(self):
        engine = AppleVisionEngine()
        with mock.patch.dict(sys.modules, {'Vision': None}):
            with self.assertLogs('usta.core.ocr.apple_vision_engine', level='ERROR') as logs:
                self.assertEqual(engine.read_text('image.png'), '')
                self.assertEqual(engine.read_text('image.png'), '')
            self.assertEqual(len(logs.output), 1)

    def test_engine_is_offered_only_on_macos(self):
        self.assertIn('Apple Vision', resolve_capabilities('Darwin', '')['OCR_ENGINES'])
        for platform in ('Linux', 'Windows'):
            self.assertNotIn('Apple Vision', resolve_capabilities(platform, '')['OCR_ENGINES'])
        with mock.patch('usta.core.ocr.ocr_manager.sys.platform', 'linux'):
            self.assertNotIn('Apple Vision', OCRManager().engines)

    @unittest.skipUnless(os.environ.get('USTA_NATIVE_TESTS') == '1' and sys.platform == 'darwin', 'Requires macOS')
    def test_manager_selects_vision_and_propagates_language(self):
        manager = OCRManager()
        manager.set_engine('Apple Vision')
        manager.set_language('ko')
        self.assertEqual(manager.current_engine_name, 'Apple Vision')
        self.assertEqual(manager.engines['Apple Vision'].language, 'ko')


@unittest.skipUnless(os.environ.get('USTA_NATIVE_TESTS') == '1' and sys.platform == 'darwin' and importlib.util.find_spec('Vision'),
                     'Requires macOS and pyobjc-framework-Vision')
class NativeVisionTests(unittest.TestCase):
    def test_recognizes_english_from_file_with_spaces(self):
        engine = AppleVisionEngine()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'OCR image.png'
            image = Image.new('RGB', (900, 180), 'white')
            font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 60)
            ImageDraw.Draw(image).text((35, 45), 'USTA Vision Test 123', font=font, fill='black')
            image.save(path)
            # Match the worker's background-thread usage, including pool cleanup.
            with ThreadPoolExecutor(max_workers=1) as executor:
                for _ in range(3):
                    text = executor.submit(engine.read_text, str(path)).result(timeout=15)
                    self.assertEqual(text, 'USTA Vision Test 123')

    def test_korean_and_auto_recognize_korean(self):
        import Vision
        request = AppleVisionEngine()._make_request(Vision)
        supported, _ = request.supportedRecognitionLanguagesAndReturnError_(None)
        if 'ko-KR' not in supported:
            self.skipTest('Korean recognition is unavailable on this macOS version')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'korean.png'
            image = Image.new('RGB', (1000, 180), 'white')
            font = ImageFont.truetype('/System/Library/Fonts/AppleSDGothicNeo.ttc', 65)
            ImageDraw.Draw(image).text((35, 40), '안녕하세요 감사합니다', font=font, fill='black')
            image.save(path)
            for language in ('ko', 'auto'):
                with self.subTest(language=language):
                    engine = AppleVisionEngine()
                    engine.set_language(language)
                    text = engine.read_text(str(path))
                    self.assertEqual(text.replace(' ', ''), '안녕하세요감사합니다')

    def test_blank_image_returns_empty_text(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'blank.png'
            Image.new('RGB', (600, 120), 'white').save(path)
            self.assertEqual(AppleVisionEngine().read_text(str(path)), '')

    def test_invalid_image_returns_empty_text_without_crashing(self):
        with self.assertLogs('usta.core.ocr.apple_vision_engine', level='ERROR'):
            self.assertEqual(AppleVisionEngine().read_text('/nonexistent/usta-image.png'), '')

    def test_unsupported_language_uses_auto_and_warns_once(self):
        import Vision
        engine = AppleVisionEngine()
        engine.set_language('zz-XX')
        with self.assertLogs('usta.core.ocr.apple_vision_engine', level='WARNING') as logs:
            request = engine._make_request(Vision)
            engine._make_request(Vision)
        self.assertEqual(len(logs.output), 1)
        supported, _ = request.supportedRecognitionLanguagesAndReturnError_(None)
        self.assertEqual(list(request.recognitionLanguages()), list(supported))
        if hasattr(request, 'automaticallyDetectsLanguage'):
            self.assertTrue(request.automaticallyDetectsLanguage())
