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
