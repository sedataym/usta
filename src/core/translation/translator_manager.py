import os
import pickle

from src.config import CUSTOM_TRANSLATION_APIS_FILE
from src.core.translation.custom_api_engine import CustomAPITranslatorEngine
from src.core.translation.google_engine import GoogleEngine
from src.core.translation.deepl_engine import DeepLTranslatorEngine

class TranslatorManager:
    def __init__(self):
        self.builtin_translators = {
            "Google": GoogleEngine(),
            "DeepL": DeepLTranslatorEngine()
        }
        self.translators = dict(self.builtin_translators)
        self.current_translator_name = "Google"
        self._source_lang = "en"
        self._target_lang = "tr"
        self.reload_custom_engines()

    def _load_custom_api_configs(self):
        if not os.path.exists(CUSTOM_TRANSLATION_APIS_FILE):
            return {}
        try:
            with open(CUSTOM_TRANSLATION_APIS_FILE, "rb") as f:
                payload = pickle.load(f)
        except Exception as e:
            print(f"Custom translation APIs load error: {e}")
            return {}

        if not isinstance(payload, dict):
            return {}
        return payload

    def reload_custom_engines(self):
        self.translators = dict(self.builtin_translators)
        configs = self._load_custom_api_configs()
        builtin_names = set(self.builtin_translators.keys())

        for raw_name, config in configs.items():
            name = str(raw_name).strip() if raw_name is not None else ""
            if not name or name in builtin_names or not isinstance(config, dict):
                continue
            endpoint = config.get("endpoint")
            if not isinstance(endpoint, str) or not endpoint.strip():
                continue
            headers = config.get("headers", {})
            if headers is None:
                headers = {}
            if not isinstance(headers, dict):
                continue
            self.translators[name] = CustomAPITranslatorEngine(name, endpoint.strip(), headers)

        if self.current_translator_name not in self.translators:
            self.current_translator_name = "Google" if "Google" in self.translators else next(iter(self.translators), "")

    def set_translator(self, name: str):
        if name in self.translators:
            self.current_translator_name = name

    def set_api_key(self, engine: str, api_key: str):
        translator = self.translators.get(engine)
        if translator and hasattr(translator, "set_api_key"):
            translator.set_api_key(api_key)

    def set_languages(self, source: str, target: str):
        self._source_lang = source
        self._target_lang = target
        for translator in self.translators.values():
            translator.set_languages(source, target)

    def get_languages(self) -> tuple[str, str]:
        return self._source_lang, self._target_lang

    def translate(self, text: str) -> str:
        translator = self.translators.get(self.current_translator_name)
        if translator:
            return translator.translate(text)
        return text

