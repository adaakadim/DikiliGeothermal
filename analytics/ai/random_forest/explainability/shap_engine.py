"""
analytics/ai/random_forest/explainability/shap_engine.py
========================================================
Core SHAP integration. Calculates SHAP values on-the-fly for real-time predictions.
"""

import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# We will lazily import shap to prevent crash if not installed
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logger.warning("SHAP library not found. Explainability will be mocked.")

from analytics.ai.random_forest.model_loader import ModelCache

class SHAPEngine:
    def __init__(self):
        self._explainer = None
        self._model_version = None

    def _ensure_explainer(self):
        """Initialize or reload the SHAP explainer if the model changed."""
        if not SHAP_AVAILABLE: return False
        
        pump_model = ModelCache.get_model("PumpFailure_RF")
        if not pump_model: return False
        
        # In a real scenario, we might want to track model hashes, but for now
        # we initialize it once or if the object changes.
        if self._explainer is None:
            try:
                # TreeExplainer is extremely fast for Random Forests
                self._explainer = shap.TreeExplainer(pump_model)
                logger.info("SHAP TreeExplainer initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize SHAP TreeExplainer: {e}")
                return False
        return True

    def calculate_shap(self, live_features: dict) -> dict:
        """
        Calculates SHAP values for a single row of live features.
        
        Returns:
            Dictionary mapping feature names to their SHAP values (influence on risk).
        """
        if not self._ensure_explainer():
            return {}

        try:
            df = pd.DataFrame([live_features])
            
            # Calculate SHAP values
            # For random forest classification, shap_values is typically a list of arrays (one for each class).
            # We want the values for Class 1 (Failure).
            shap_vals = self._explainer.shap_values(df)
            
            # Depending on shap version and model type, shap_vals could be a list or a single array
            if isinstance(shap_vals, list):
                class_1_shap = shap_vals[1][0]  # First row, Class 1
            elif len(shap_vals.shape) == 3:
                # Newer shap versions might return (1, num_features, num_classes)
                class_1_shap = shap_vals[0, :, 1]
            else:
                # Single array fallback
                class_1_shap = shap_vals[0]

            # Map back to feature names
            features = list(df.columns)
            shap_dict = {feat: float(val) for feat, val in zip(features, class_1_shap)}
            return shap_dict
            
        except Exception as e:
            logger.error(f"Error calculating SHAP values: {e}")
            return {}
