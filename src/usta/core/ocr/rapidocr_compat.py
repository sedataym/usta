"""Compatibility adapter for rapidocr-onnxruntime 1.2.x.

The installed version exposes no public thread-count setting.
"""
import logging
logger = logging.getLogger(__name__)

def patch_ort_session(cpu_threads: int):
    from onnxruntime import GraphOptimizationLevel, InferenceSession, SessionOptions
    from rapidocr_onnxruntime.utils import OrtInferSession, get_available_providers, get_device


    def limited_init(session_self, config):
        sess_opt = SessionOptions()
        sess_opt.log_severity_level = 4
        sess_opt.enable_cpu_mem_arena = False
        sess_opt.graph_optimization_level = GraphOptimizationLevel.ORT_ENABLE_ALL
        sess_opt.intra_op_num_threads = cpu_threads
        sess_opt.inter_op_num_threads = 1

        cpu_ep = "CPUExecutionProvider"
        cpu_provider_options = {
            "arena_extend_strategy": "kSameAsRequested",
            "intra_op_num_threads": str(cpu_threads),
        }

        cuda_ep = "CUDAExecutionProvider"
        cuda_provider_options = {
            "device_id": 0,
            "arena_extend_strategy": "kNextPowerOfTwo",
            "cudnn_conv_algo_search": "EXHAUSTIVE",
            "do_copy_in_default_stream": True,
        }

        ep_list = []
        if (
            config["use_cuda"]
            and get_device() == "GPU"
            and cuda_ep in get_available_providers()
        ):
            ep_list = [(cuda_ep, cuda_provider_options)]
        ep_list.append((cpu_ep, cpu_provider_options))

        session_self._verify_model(config["model_path"])
        session_self.session = InferenceSession(
            config["model_path"],
            sess_options=sess_opt,
            providers=ep_list,
        )

    if getattr(OrtInferSession.__init__, "_usta_cpu_limited", False):
        logger.info("RapidOCREngine: OrtInferSession already patched, skipping")
        return

    limited_init._usta_cpu_limited = True
    OrtInferSession.__init__ = limited_init
    logger.info("RapidOCREngine: OrtInferSession monkey-patched for CPU thread limiting")

