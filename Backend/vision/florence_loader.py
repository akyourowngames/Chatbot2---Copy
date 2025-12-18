import os
import logging
import torch
from transformers import AutoProcessor, AutoModelForCausalLM

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
MODEL_ID = "microsoft/Florence-2-base"
# Pin a stable revision that works with the new task‑based API
REVISION = "refs/pr/6"
CACHE_DIR = os.path.join(os.getcwd(), "models", "vision", "florence2")

# ----------------------------------------------------------------------
# Global singleton objects
# ----------------------------------------------------------------------
_model = None
_processor = None
_device = None


def get_device() -> str:
    """Detect the best device (cuda > mps > cpu)."""
    global _device
    if _device is None:
        if torch.cuda.is_available():
            _device = "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            _device = "mps"
        else:
            _device = "cpu"
    return _device


def _configure_torch_backends():
    """Force eager attention – disables all SDPA/Flash‑Attention paths."""
    if hasattr(torch.backends, "cuda"):
        try:
            if hasattr(torch.backends.cuda, "enable_flash_sdp"):
                torch.backends.cuda.enable_flash_sdp(False)
            if hasattr(torch.backends.cuda, "enable_mem_efficient_sdp"):
                torch.backends.cuda.enable_mem_efficient_sdp(False)
            if hasattr(torch.backends.cuda, "enable_math_sdp"):
                torch.backends.cuda.enable_math_sdp(True)
        except Exception as exc: 
            logger.debug(f"[VISION] Torch backend tweak failed: {exc}")


def load_florence_model():
    """
    Load (or retrieve cached) the Florence‑2 model and its processor.
    Returns
    -------
    tuple
        (model, processor) – both ready for inference on the detected device.
    """
    global _model, _processor

    if _model is not None and _processor is not None:
        return _model, _processor

    try:
        device = get_device()
        logger.info(f"[VISION] Loading Florence‑2 on {device}")
        logger.info(f"[VISION] Cache directory: {CACHE_DIR}")

        _configure_torch_backends()
        os.makedirs(CACHE_DIR, exist_ok=True)

        # --------------------------------------------------------------
        # Processor
        # --------------------------------------------------------------
        _processor = AutoProcessor.from_pretrained(
            MODEL_ID,
            trust_remote_code=True,
            cache_dir=CACHE_DIR,
        )

        # --------------------------------------------------------------
        # Model – eager attention, dtype chosen per device
        # --------------------------------------------------------------
        torch_dtype = torch.float16 if device == "cuda" else torch.float32

        logger.info("[VISION] Initializing model with attn_implementation='eager'")
        _model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            trust_remote_code=True,
            torch_dtype=torch_dtype,
            attn_implementation="eager",   # crucial – disables SDPA
            cache_dir=CACHE_DIR,
        ).to(device)

        logger.info("[VISION] Florence‑2 model loaded successfully")
        return _model, _processor

    except Exception as exc:
        logger.error(f"[VISION] Model load failure: {exc}")
        _model, _processor = None, None
        raise RuntimeError(f"Failed to load Florence‑2 model: {exc}")


def release_florence_model():
    """Free GPU/CPU memory – useful for long‑running services."""
    global _model, _processor
    _model, _processor = None, None
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    logger.info("[VISION] Florence‑2 model released")
