from usta.application.results import TranslationRequest, TranslationResult
from usta.core.registry import TRANSLATOR_FACTORIES, LazyEngines


class TranslatorManager:
    def __init__(self):
        self._source_lang = "en"
        self._target_lang = "tr"
        self._api_keys = {}
        self.translators = LazyEngines(TRANSLATOR_FACTORIES, self._initialize)
        self.current_translator_name = "Google"

    def _initialize(self, name, translator):
        translator.set_languages(self._source_lang, self._target_lang)
        if name in self._api_keys and hasattr(translator, "set_api_key"):
            translator.set_api_key(self._api_keys[name])

    def set_translator(self, name: str):
        if name in self.translators:
            self.current_translator_name = name

    def set_api_key(self, engine: str, api_key: str):
        self._api_keys[engine] = api_key
        translator = self.translators.instances.get(engine)
        if translator and hasattr(translator, "set_api_key"):
            translator.set_api_key(api_key)

    def set_languages(self, source: str, target: str):
        self._source_lang, self._target_lang = source, target
        for translator in self.translators.instances.values():
            translator.set_languages(source, target)

    def get_languages(self) -> tuple[str, str]:
        return self._source_lang, self._target_lang

    def translate(self, text: str) -> str:
        return self.translators[self.current_translator_name].translate(text)

    def translate_request(self, request: TranslationRequest) -> TranslationResult:
        self.set_translator(request.engine_name)
        self.set_languages(request.source_lang, request.target_lang)
        return TranslationResult(
            self.translate(request.text),
            request.source_lang,
            request.target_lang,
            request.engine_name,
            request.session_id,
        )
