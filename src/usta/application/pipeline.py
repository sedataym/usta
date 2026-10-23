"""Single-owner capture loop with immutable translation jobs."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import logging
import threading
import time

from usta.application.results import TranslationRequest
from usta.application.settings import AppSettings
from usta.config import get_language_code
from usta.core.exceptions import PortalCanceledError
from usta.core.ocr.ocr_manager import OCRManager
from usta.core.translation.translator_manager import TranslatorManager

logger = logging.getLogger(__name__)

class Pipeline:
    LOOP_SLEEP_SECONDS = 0.2

    def __init__(self, *, capture_factory, publisher, image_path, on_translation,
                 on_error, ocr_factory=OCRManager, translator_factory=TranslatorManager,
                 rect_factory=tuple, preprocess=None, on_performance=lambda value: None,
                 on_translating=lambda value: None):
        self.capture_factory = capture_factory
        self.publisher = publisher
        self.image_path = image_path
        self.on_translation = on_translation
        self.on_error = on_error
        self.ocr_factory = ocr_factory
        self.translator_factory = translator_factory
        self.rect_factory = rect_factory
        self.preprocess = preprocess
        self.on_performance = on_performance
        self.on_translating = on_translating
        self._settings = AppSettings()
        self._lock = threading.RLock()
        self._stopped = threading.Event()
        self._stopped.set()
        self._session = 0
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='usta-translation')
        self._future = None
        self._job = None

    @property
    def settings(self):
        with self._lock:
            return deepcopy(self._settings)

    def configure(self, settings: AppSettings) -> None:
        with self._lock:
            self._settings = deepcopy(settings)
            self._session += 1

    def start(self) -> None:
        with self._lock:
            self._session += 1
            self._stopped.clear()

    def stop(self) -> None:
        with self._lock:
            self._session += 1
            self._stopped.set()

    def close(self) -> None:
        self.stop()
        self._executor.shutdown(wait=False, cancel_futures=True)

    def _translate(self, request, keys):
        # This manager is used only by the translation owner thread, never by UI.
        translator = self.translator_factory()
        for name, key in keys.items():
            translator.set_api_key(name, key)
        return translator.translate_request(request)

    def _collect(self):
        if self._future is None or not self._future.done():
            return
        future, job = self._future, self._job
        self._future = self._job = None
        with self._lock:
            valid = not self._stopped.is_set() and job.session_id == self._session
            if not valid:
                return
            self.on_translating(False)
            try:
                result = future.result()
            except Exception as exc:
                self.on_error(str(exc))
                return
            self.on_translation(result.translated_text)
            self.publisher.broadcast(original=job.text, translated=result.translated_text,
                                     source_lang=job.source_lang, target_lang=job.target_lang,
                                     engine=job.engine_name)

    def run(self) -> None:
        capture = None
        applied = -1
        capture_name = None
        last_text = ''
        ocr = self.ocr_factory()
        try:
            self.publisher.start()
            while not self._stopped.is_set():
                started = time.perf_counter()
                try:
                    with self._lock:
                        settings, session = deepcopy(self._settings), self._session
                    if session != applied:
                        if capture is None or capture_name != settings.screenshot_engine:
                            if capture is not None:
                                capture.close()
                            capture = self.capture_factory(settings.screenshot_engine)
                            capture_name = settings.screenshot_engine
                        ocr.set_engine(settings.ocr_engine)
                        ocr.set_language(get_language_code(settings.source_lang, settings.source_lang))
                        applied = session
                        last_text = ''
                    self._collect()
                    if self._stopped.is_set():
                        break
                    if capture.capture(self.rect_factory(settings.capture_rect), self.image_path, settings.dpi_scale):
                        if settings.ocr_engine == 'Tesseract' and self.preprocess:
                            self.preprocess(self.image_path, self.image_path)
                        text = ocr.read_result(self.image_path).text
                        with self._lock:
                            if (session == self._session and not self._stopped.is_set()
                                    and len(text) > 2 and text != last_text and self._future is None):
                                request = TranslationRequest(text,
                                    get_language_code(settings.source_lang, settings.source_lang),
                                    get_language_code(settings.target_lang, settings.target_lang),
                                    settings.translator_engine, session)
                                self._job = request
                                self._future = self._executor.submit(self._translate, request, settings.translator_api_keys)
                                last_text = text
                                self.on_translating(True)
                    self.on_performance(time.perf_counter() - started)
                except PortalCanceledError:
                    self.stop()
                except Exception as exc:
                    logger.exception('Capture/OCR pipeline failed')
                    self.on_error(str(exc))
                self._stopped.wait(self.LOOP_SLEEP_SECONDS)
        except Exception as exc:
            self.on_error(str(exc))
        finally:
            try:
                if capture is not None:
                    capture.close()
            finally:
                self.publisher.stop()
                self.on_translating(False)
