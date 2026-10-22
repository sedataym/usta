import unittest
from unittest import mock

import pytest

httpx = pytest.importorskip("httpx")

from src.core.translation.custom_api_engine import CustomAPITranslatorEngine


class CustomAPITranslatorEngineTests(unittest.IsolatedAsyncioTestCase):
    def test_extracts_translated_text_json_field(self):
        response = httpx.Response(200, json={"translated_text": " merhaba "})

        self.assertEqual(CustomAPITranslatorEngine._extract_text_from_response(response), "merhaba")

    def test_falls_back_to_text_json_field(self):
        response = httpx.Response(200, json={"text": " selam "})

        self.assertEqual(CustomAPITranslatorEngine._extract_text_from_response(response), "selam")

    def test_falls_back_to_translation_json_field(self):
        response = httpx.Response(200, json={"translation": " merhaba dünya "})

        self.assertEqual(CustomAPITranslatorEngine._extract_text_from_response(response), "merhaba dünya")

    def test_falls_back_to_result_json_field(self):
        response = httpx.Response(200, json={"result": " çeviri "})

        self.assertEqual(CustomAPITranslatorEngine._extract_text_from_response(response), "çeviri")

    def test_extracts_plain_text_response(self):
        response = httpx.Response(200, text=" çeviri ")

        self.assertEqual(CustomAPITranslatorEngine._extract_text_from_response(response), "çeviri")

    def test_unexpected_json_returns_empty_string(self):
        response = httpx.Response(200, json={"items": ["abc"]})

        self.assertEqual(CustomAPITranslatorEngine._extract_text_from_response(response), "")

    async def test_async_translate_posts_json_and_headers(self):
        captured = {}

        class FakeAsyncClient:
            def __init__(self, timeout):
                self.timeout = timeout

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            async def post(self, endpoint, json, headers):
                captured["endpoint"] = endpoint
                captured["json"] = json
                captured["headers"] = headers
                request = httpx.Request("POST", endpoint)
                return httpx.Response(200, json={"translated_text": "merhaba"}, request=request)

        engine = CustomAPITranslatorEngine(
            "My Translator",
            "https://example.com/translate",
            headers={"Authorization": "Bearer token", "Content-Type": "application/json"},
        )
        engine.set_languages("en", "tr")
        with mock.patch("src.core.translation.custom_api_engine.httpx.AsyncClient", FakeAsyncClient):
            text = await engine._translate_async("hello")

        self.assertEqual(text, "merhaba")
        self.assertEqual(captured["endpoint"], "https://example.com/translate")
        self.assertEqual(captured["json"], {"text": "hello", "source_lang": "en", "target_lang": "tr"})
        self.assertEqual(captured["headers"]["Authorization"], "Bearer token")
        self.assertNotIn("Content-Type", captured["headers"])


if __name__ == "__main__":
    unittest.main()
