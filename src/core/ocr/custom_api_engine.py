import asyncio
import os

import httpx

from src.core.ocr.base_ocr import BaseOCREngine


class CustomAPIOCREngine(BaseOCREngine):
    def __init__(self, name, endpoint, headers=None, timeout=30):
        self.name = name
        self.endpoint = endpoint
        self.headers = dict(headers or {})
        self.timeout = timeout
        self.lang = None

    def set_language(self, lang_code: str):
        self.lang = lang_code

    def read_text(self, image_path: str) -> str:
        try:
            return asyncio.run(self._read_text_async(image_path))
        except Exception as e:
            print(f"Custom OCR API error ({self.name}): {e}")
            return ""

    async def _read_text_async(self, image_path: str) -> str:
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        files = {
            "image": (
                os.path.basename(image_path),
                image_bytes,
                "image/jpeg",
            )
        }
        headers = self._request_headers()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(self.endpoint, files=files, headers=headers)
            response.raise_for_status()
            return self._extract_text_from_response(response)

    def _request_headers(self):
        headers = dict(self.headers)
        for key in list(headers.keys()):
            if key.lower() == "content-type":
                del headers[key]
        return headers

    @staticmethod
    def _extract_text_from_response(response) -> str:
        try:
            payload = response.json()
        except Exception:
            return response.text.strip()

        if not isinstance(payload, dict):
            return ""

        text = payload.get("text")
        if isinstance(text, str):
            return text.strip()

        return ""
