import asyncio

import httpx

from src.core.translation.base_translator import BaseTranslator


class CustomAPITranslatorEngine(BaseTranslator):
    def __init__(self, name, endpoint, headers=None, timeout=30):
        self.name = name
        self.endpoint = endpoint
        self.headers = dict(headers or {})
        self.timeout = timeout
        self.source = "en"
        self.target = "tr"

    def set_languages(self, source: str, target: str):
        self.source = source
        self.target = target

    def translate(self, text: str) -> str:
        try:
            return asyncio.run(self._translate_async(text))
        except Exception as e:
            print(f"Custom translation API error ({self.name}): {e}")
            return ""

    async def _translate_async(self, text: str) -> str:
        payload = {
            "text": text,
            "source_lang": self.source,
            "target_lang": self.target,
        }
        headers = self._request_headers()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(self.endpoint, json=payload, headers=headers)
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

        for key in ("translated_text", "text", "translation", "result"):
            value = payload.get(key)
            if isinstance(value, str):
                return value.strip()

        return ""
