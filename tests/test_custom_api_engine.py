import tempfile
import unittest
from unittest import mock

import pytest

httpx = pytest.importorskip("httpx")

from src.core.ocr.custom_api_engine import CustomAPIOCREngine


class CustomAPIOCREngineTests(unittest.IsolatedAsyncioTestCase):
    def test_extracts_text_json_field(self):
        response = httpx.Response(200, json={"text": " abc "})

        self.assertEqual(CustomAPIOCREngine._extract_text_from_response(response), "abc")

    def test_result_json_field_is_ignored(self):
        response = httpx.Response(200, json={"result": "abc"})

        self.assertEqual(CustomAPIOCREngine._extract_text_from_response(response), "")

    def test_nested_data_text_json_field_is_ignored(self):
        response = httpx.Response(200, json={"data": {"text": "abc"}})

        self.assertEqual(CustomAPIOCREngine._extract_text_from_response(response), "")

    def test_extracts_plain_text_response(self):
        response = httpx.Response(200, text=" abc ")

        self.assertEqual(CustomAPIOCREngine._extract_text_from_response(response), "abc")

    def test_unexpected_json_returns_empty_string(self):
        response = httpx.Response(200, json={"items": ["abc"]})

        self.assertEqual(CustomAPIOCREngine._extract_text_from_response(response), "")

    async def test_async_read_posts_image_and_headers(self):
        captured = {}

        class FakeAsyncClient:
            def __init__(self, timeout):
                self.timeout = timeout

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            async def post(self, endpoint, files, headers):
                captured["endpoint"] = endpoint
                captured["files"] = files
                captured["headers"] = headers
                request = httpx.Request("POST", endpoint)
                return httpx.Response(200, json={"text": "hello"}, request=request)

        engine = CustomAPIOCREngine(
            "My OCR",
            "https://example.com/ocr",
            headers={"Authorization": "Bearer token", "Content-Type": "application/json"},
        )
        with tempfile.NamedTemporaryFile(suffix=".jpeg") as image_file:
            image_file.write(b"image-bytes")
            image_file.flush()
            with mock.patch("src.core.ocr.custom_api_engine.httpx.AsyncClient", FakeAsyncClient):
                text = await engine._read_text_async(image_file.name)

        self.assertEqual(text, "hello")
        self.assertEqual(captured["endpoint"], "https://example.com/ocr")
        self.assertIn("image", captured["files"])
        filename, image_bytes, content_type = captured["files"]["image"]
        self.assertTrue(filename.endswith(".jpeg"))
        self.assertEqual(image_bytes, b"image-bytes")
        self.assertEqual(content_type, "image/jpeg")
        self.assertEqual(captured["headers"]["Authorization"], "Bearer token")
        self.assertNotIn("Content-Type", captured["headers"])


if __name__ == "__main__":
    unittest.main()
