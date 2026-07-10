"""
analytics/ai/random_forest/model_loader.py
==========================================
Provides an efficient, cached loading mechanism for real-time SCADA integration.
Ensures models are only loaded from disk once.
"""

import logging
import time
from analytics.ai.random_forest.version_manager import load_latest_model

logger = logging.getLogger(__name__)

class ModelCache:
    """Singleton cache for loaded AI models."""
    _models = {}
    _stats = {}

    @classmethod
    def get_model(cls, model_name: str):
        """Returns the loaded model, fetching from disk if not already cached."""
        if model_name not in cls._models:
            start_t = time.perf_counter()
            cls._stats[model_name] = {
                "load_status": "Loading",
                "load_time_ms": 0.0,
                "error": None,
                "total_predictions": 0,
                "total_inference_ms": 0.0,
                "last_prediction_ts": "Never"
            }
            try:
                model = load_latest_model(model_name)
                load_ms = (time.perf_counter() - start_t) * 1000.0
                if model is not None:
                    cls._models[model_name] = model
                    cls._stats[model_name]["load_status"] = "Ready"
                    cls._stats[model_name]["load_time_ms"] = load_ms
                else:
                    cls._stats[model_name]["load_status"] = "Inactive"
                    logger.error(f"Failed to load model into cache: {model_name}")
            except Exception as e:
                cls._stats[model_name]["load_status"] = "Error"
                cls._stats[model_name]["error"] = str(e)
                logger.error(f"Error loading model {model_name}: {e}")
                
        return cls._models.get(model_name)

    @classmethod
    def update_inference_stats(cls, model_name: str, latency_ms: float, timestamp: str):
        """Updates real-time performance tracking."""
        if model_name in cls._stats:
            cls._stats[model_name]["total_predictions"] += 1
            cls._stats[model_name]["total_inference_ms"] += latency_ms
            cls._stats[model_name]["last_prediction_ts"] = timestamp

    @classmethod
    def get_model_stats(cls, model_name: str):
        return cls._stats.get(model_name, {})

    @classmethod
    def clear_cache(cls):
        """Forces models to be reloaded from disk on next request."""
        cls._models.clear()
        cls._stats.clear()
        logger.info("Model cache cleared.")
