from dataclasses import replace
import threading
import time
import unittest
from unittest.mock import Mock
from usta.application.pipeline import Pipeline
from usta.application.settings import AppSettings

class PipelineLifecycleTests(unittest.TestCase):
    def make_pipeline(self):
        entered, release, finished = threading.Event(), threading.Event(), threading.Event()
        translator=Mock()
        def translate(request):
            from usta.application.results import TranslationResult
            entered.set();release.wait(3)
            finished.set()
            return TranslationResult('translated',request.source_lang,request.target_lang,request.engine_name,request.session_id)
        translator.translate_request.side_effect=translate
        capture=Mock();capture.capture.return_value=True
        ocr=Mock();ocr.read_result.return_value=Mock(text='hello')
        publisher=Mock();result=Mock();errors=Mock()
        pipeline=Pipeline(ocr_factory=lambda:ocr, capture_factory=lambda name:capture,
                          translator_factory=lambda:translator, publisher=publisher,
                          on_translation=result, on_error=errors, image_path='/tmp/fake.jpeg')
        return pipeline,entered,release,finished,result,publisher,errors

    def test_stop_does_not_wait_for_api_and_suppresses_late_result(self):
        pipeline,entered,release,finished,result,publisher,errors=self.make_pipeline()
        thread=threading.Thread(target=pipeline.run)
        pipeline.start();thread.start()
        self.assertTrue(entered.wait(2))
        start=time.monotonic();pipeline.stop();thread.join(1)
        self.assertFalse(thread.is_alive())
        self.assertLess(time.monotonic()-start,1)
        release.set();self.assertTrue(finished.wait(2))
        pipeline.close()
        result.assert_not_called();publisher.broadcast.assert_not_called()

    def test_reconfigure_discards_previous_session_metadata(self):
        pipeline,entered,release,finished,result,publisher,errors=self.make_pipeline()
        pipeline.start();thread=threading.Thread(target=pipeline.run);thread.start()
        self.assertTrue(entered.wait(2))
        pipeline.configure(replace(pipeline.settings,target_lang='German'))
        release.set();self.assertTrue(finished.wait(2))
        pipeline.stop();thread.join(2);pipeline.close()
        result.assert_not_called();publisher.broadcast.assert_not_called()

    def test_engine_error_never_becomes_translation(self):
        from usta.application.results import EngineError
        pipeline,entered,release,finished,result,publisher,errors=self.make_pipeline()
        pipeline.translator_factory=lambda: Mock(translate_request=Mock(side_effect=EngineError('api','failed')))
        errors.side_effect=lambda message:pipeline.stop()
        pipeline.start();pipeline.run();pipeline.close()
        errors.assert_called_once();result.assert_not_called();publisher.broadcast.assert_not_called()
