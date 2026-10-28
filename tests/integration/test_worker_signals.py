import threading
import unittest

from PySide6.QtCore import QCoreApplication

from usta.application.worker import OCRWorker


class WorkerSignalsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def test_queued_result_is_discarded_if_stopped_before_gui_delivery(self):
        worker = OCRWorker()
        self.addCleanup(worker.close)
        received = []
        worker.new_translation.connect(received.append)
        worker.pipeline.start()
        producer = threading.Thread(target=lambda: worker.pipeline.on_translation("old result"))
        producer.start()
        producer.join()
        worker.stop()
        self.app.processEvents()
        self.assertEqual(received, [])

    def test_repeated_start_does_not_schedule_unrequested_restart(self):
        worker = OCRWorker()
        self.addCleanup(worker.close)
        worker.pipeline.start()
        from unittest.mock import patch

        with patch.object(worker, "isRunning", return_value=True):
            worker.start()
        self.assertFalse(worker._restart_requested)

    def test_queued_timings_are_discarded_after_stop(self):
        worker = OCRWorker()
        self.addCleanup(worker.close)
        received = []
        worker.timings_update.connect(received.append)
        worker.pipeline.start()
        producer = threading.Thread(target=lambda: worker.pipeline.on_timings("old timings"))
        producer.start()
        producer.join()
        worker.stop()
        self.app.processEvents()
        self.assertEqual(received, [])

    def test_fatal_capture_error_reaches_gui_after_pipeline_stops(self):
        from unittest.mock import Mock

        from usta.core.exceptions import ScreenCapturePermissionError

        worker = OCRWorker()
        self.addCleanup(worker.close)
        received = []
        worker.error_occurred.connect(received.append)
        capture = Mock()
        capture.capture.side_effect = ScreenCapturePermissionError("Screen Recording unavailable")
        worker.pipeline.capture_factory = lambda name: capture
        worker.pipeline.ocr_factory = Mock
        worker.pipeline.publisher = Mock()
        worker.pipeline.start()
        producer = threading.Thread(target=worker.pipeline.run)
        producer.start()
        producer.join(timeout=2)
        self.assertFalse(producer.is_alive())
        self.app.processEvents()
        self.assertEqual(received, ["Screen Recording unavailable"])

    def test_queued_error_is_discarded_after_a_new_session_starts(self):
        worker = OCRWorker()
        self.addCleanup(worker.close)
        received = []
        worker.error_occurred.connect(received.append)
        worker.pipeline.start()
        producer = threading.Thread(target=lambda: worker.pipeline.on_error("old error"))
        producer.start()
        producer.join()
        worker.stop()
        worker.pipeline.start()
        self.app.processEvents()
        self.assertEqual(received, [])
