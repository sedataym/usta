import unittest
from unittest.mock import Mock, patch

from usta.core.ocr.rapidocr_compat import patch_ort_session


class RapidOCRCompatibilityTests(unittest.TestCase):
    def test_patch_preserves_thread_count_and_installs_only_once(self):
        import onnxruntime
        from rapidocr_onnxruntime.utils import OrtInferSession

        original = OrtInferSession.__init__
        self.addCleanup(setattr, OrtInferSession, "__init__", original)
        with patch.object(onnxruntime, "InferenceSession") as inference:
            patch_ort_session(1)
            replacement = OrtInferSession.__init__
            patch_ort_session(1)
            self.assertIs(OrtInferSession.__init__, replacement)
            replacement(Mock(), {"use_cuda": False, "model_path": "fake.onnx"})
            options = inference.call_args.kwargs["sess_options"]
            self.assertEqual(options.intra_op_num_threads, 1)
            self.assertEqual(options.inter_op_num_threads, 1)
            self.assertEqual(inference.call_args.kwargs["providers"][0][0], "CPUExecutionProvider")
