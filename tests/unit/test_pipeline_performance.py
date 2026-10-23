"""Performance reflects the capture-to-translation latency of one valid job."""

import unittest
from concurrent.futures import Future
from dataclasses import replace
from unittest.mock import Mock, patch

from usta.application.pipeline import Pipeline
from usta.application.results import TranslationResult


class DeferredExecutor:
    def submit(self, function, *args):
        self.function, self.args = function, args
        self.future = Future()
        return self.future

    def complete(self):
        self.future.set_result(self.function(*self.args))

    def shutdown(self, **kwargs):
        pass


class PipelinePerformanceTests(unittest.TestCase):
    def make_pipeline(self):
        clock = [0.0]
        capture = Mock()
        capture.capture.side_effect = lambda *args: clock.__setitem__(0, 0.2) or True
        ocr = Mock()

        def read(path):
            clock[0] = 0.5
            return Mock(text="hello")

        ocr.read_result.side_effect = read
        translator = Mock()

        def translate(request):
            clock[0] = 2.0
            return TranslationResult("merhaba", "en", "tr", "Google", request.session_id)

        translator.translate_request.side_effect = translate
        performance = Mock()
        pipeline = Pipeline(
            capture_factory=lambda name: capture,
            publisher=Mock(),
            ocr_factory=lambda: ocr,
            translator_factory=lambda: translator,
            image_path="unused",
            on_translation=Mock(),
            on_error=Mock(),
            on_performance=performance,
        )
        pipeline._executor.shutdown(wait=False)
        executor = DeferredExecutor()
        pipeline._executor = executor
        self.addCleanup(pipeline.close)
        return pipeline, executor, clock, performance

    def test_capture_ocr_and_translation_are_timed_without_polling_delay(self):
        pipeline, executor, clock, performance = self.make_pipeline()
        early = []

        def between_iterations(timeout):
            early.extend(performance.call_args_list)
            executor.complete()
            clock[0] = 20.0  # Late collection must not inflate API response time.

        performance.side_effect = lambda duration: pipeline.stop()
        pipeline.start()
        with (
            patch("usta.application.pipeline.time.perf_counter", side_effect=lambda: clock[0]),
            patch.object(pipeline._stopped, "wait", side_effect=between_iterations),
        ):
            pipeline.run()
        self.assertEqual(early, [])
        performance.assert_called_once_with(2.0)  # 0.2 capture + 0.3 OCR + 1.5 translation.

    def test_stale_translation_does_not_update_performance(self):
        pipeline, executor, clock, performance = self.make_pipeline()

        def between_iterations(timeout):
            executor.complete()
            pipeline.configure(replace(pipeline.settings, target_lang="German"))
            pipeline._collect()
            pipeline.stop()

        pipeline.start()
        with (
            patch("usta.application.pipeline.time.perf_counter", side_effect=lambda: clock[0]),
            patch.object(pipeline._stopped, "wait", side_effect=between_iterations),
        ):
            pipeline.run()
        performance.assert_not_called()

    def test_unchanged_text_does_not_overwrite_total_with_ocr_only_duration(self):
        pipeline, executor, clock, performance = self.make_pipeline()
        waits = []

        def between_iterations(timeout):
            waits.append(timeout)
            if len(waits) == 1:
                executor.complete()
            else:
                pipeline.stop()

        pipeline.start()
        with (
            patch("usta.application.pipeline.time.perf_counter", side_effect=lambda: clock[0]),
            patch.object(pipeline._stopped, "wait", side_effect=between_iterations),
        ):
            pipeline.run()
        performance.assert_called_once_with(2.0)
