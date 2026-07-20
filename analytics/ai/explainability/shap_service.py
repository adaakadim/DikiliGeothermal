"""
analytics/ai/explainability/shap_service.py
===========================================
Enterprise SHAP Explainability Service.
Calculates real-time dynamic explanations for the active Random Forest models.
"""

import logging
import hashlib
import json
from typing import Dict, Any, List, Tuple
try:
    import pandas as pd
except ImportError:
    class MockPandas:
        def DataFrame(self, *args, **kwargs): return None
    pd = MockPandas()

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

from analytics.ai.random_forest.model_loader import ModelCache

logger = logging.getLogger(__name__)

class ShapService:
    def __init__(self):
        self._cache = {}
        self._explainer = None
        self._current_model = None

    def _get_active_model(self):
        # Always use the live active model
        model = ModelCache.get_model("PumpFailure_RF")
        if model != self._current_model:
            self._current_model = model
            self._explainer = None
            self._cache.clear()
        return model

    def _get_explainer(self, model):
        if not SHAP_AVAILABLE or not model:
            return None
        if self._explainer is None:
            try:
                # TreeExplainer is highly optimized for RandomForest
                self._explainer = shap.TreeExplainer(model)
            except Exception as e:
                logger.error(f"Failed to initialize SHAP explainer: {e}")
                return None
        return self._explainer

    def _hash_features(self, features: Dict[str, float]) -> str:
        sorted_feats = tuple(sorted((k, float(v)) for k, v in features.items() if isinstance(v, (int, float))))
        return hashlib.md5(json.dumps(sorted_feats).encode('utf-8')).hexdigest()

    def predict(self, features: Dict[str, float]) -> int:
        model = self._get_active_model()
        if not model: return 0
        df = pd.DataFrame([features])
        if hasattr(model, "feature_names_in_"):
            for col in model.feature_names_in_:
                if col not in df.columns:
                    alt = col.replace("", "°")
                    df[col] = features.get(alt, 0.0)
            df = df[list(model.feature_names_in_)]
        try:
            return int(model.predict(df)[0])
        except Exception:
            return 0

    def predict_proba(self, features: Dict[str, float]) -> List[float]:
        model = self._get_active_model()
        if not model: return [1.0, 0.0]
        df = pd.DataFrame([features])
        if hasattr(model, "feature_names_in_"):
            for col in model.feature_names_in_:
                if col not in df.columns:
                    alt = col.replace("", "°")
                    df[col] = features.get(alt, 0.0)
            df = df[list(model.feature_names_in_)]
        if hasattr(model, "predict_proba"):
            try:
                return model.predict_proba(df)[0].tolist()
            except Exception:
                pass
        return [1.0, 0.0]

    def compute_shap_values(self, features: Dict[str, float]) -> Dict[str, float]:
        """Returns raw SHAP values mapped to feature names."""
        if not SHAP_AVAILABLE:
            return {}
            
        model = self._get_active_model()
        explainer = self._get_explainer(model)
        if not explainer or not model:
            return {}

        feat_hash = self._hash_features(features)
        if feat_hash in self._cache:
            return self._cache[feat_hash]

        df = pd.DataFrame([features])
        if hasattr(model, "feature_names_in_"):
            for col in model.feature_names_in_:
                if col not in df.columns:
                    alt = col.replace("", "°")
                    df[col] = features.get(alt, 0.0)
            df = df[list(model.feature_names_in_)]

        try:
            shap_vals = explainer.shap_values(df)
            import numpy as np
            
            # Extract values based on returned format
            if hasattr(shap_vals, "values"):
                v = shap_vals.values
            elif isinstance(shap_vals, list):
                v = shap_vals[-1] # Assume last class is positive
            else:
                v = shap_vals
                
            v = np.array(v)
            
            # Target a 1D array of length (n_features)
            # If shape is (n_samples, n_features, n_classes), grab [0, :, -1]
            if len(v.shape) == 3:
                vals = v[0, :, -1]
            # If shape is (n_samples, n_features), grab [0, :]
            elif len(v.shape) == 2:
                vals = v[0, :]
            else:
                vals = v.flatten()
            
            result = {col: float(val) for col, val in zip(df.columns, vals)}
            self._cache[feat_hash] = result
            return result
        except Exception as e:
            logger.error(f"Failed to compute SHAP values: {e}")
            return {}

    def top_features(self, features: Dict[str, float], top_n: int = 5) -> List[Tuple[str, float]]:
        """Returns Top N features sorted descending by absolute SHAP impact."""
        shap_vals = self.compute_shap_values(features)
        if not shap_vals:
            return []
        
        sorted_feats = sorted(shap_vals.items(), key=lambda x: abs(x[1]), reverse=True)
        return sorted_feats[:top_n]

    def feature_importance(self, features: Dict[str, float]) -> List[Tuple[str, float]]:
        """Alias for top_features returning all features."""
        shap_vals = self.compute_shap_values(features)
        if not shap_vals: return []
        return sorted(shap_vals.items(), key=lambda x: abs(x[1]), reverse=True)

    def operator_explanation(self, features: Dict[str, float]) -> str:
        """Returns the dynamically formatted operator string using SHAP values."""
        if not SHAP_AVAILABLE or not self._get_active_model():
            return "Explainability unavailable\nModel unavailable or missing dependency."

        probs = self.predict_proba(features)
        risk = float(probs[1] * 100.0) if len(probs) > 1 else 0.0

        top_feats = self.top_features(features, top_n=5)
        
        if not top_feats:
            return "Explainability unavailable\nSHAP calculation failed."

        lines = []
        lines.append(f"Pump Failure Risk:\n{risk:.0f}%\n")
        lines.append("Main contributors\n")
        
        all_shap = self.compute_shap_values(features)
        total_var = sum(abs(v) for v in all_shap.values()) if all_shap else 1.0

        for feat, val in top_feats:
            impact = (val / total_var) * 100.0
            
            # Clean up feature name for operator readability
            clean_feat = feat.replace(" (A)", "").replace(" (°C)", "").replace(" (bar)", "").replace(" (m3/h)", "").replace(" (mm/s)", "")
            if impact >= 0:
                lines.append(f"{clean_feat}\n+{impact:.0f}%")
            else:
                lines.append(f"{clean_feat}\n{impact:.0f}%")
                
        return "\n".join(lines)

    def generate_explanation(self, target_id: str, features: Dict[str, float], ai_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Drop-in replacement wrapper for the legacy HeuristicExplainer interface.
        Maps SHAP values into the exact dictionary format expected by the UI.
        """
        top_feats = self.top_features(features, top_n=5)
        operator_text = self.operator_explanation(features)
        
        if not top_feats:
            return {
                "ranked_variables": [],
                "root_cause_chain": ["Explainability Unavailable"],
                "engineering_explanation": "Model unavailable or SHAP dependency missing.",
                "recommended_actions": ["Verify model deployment."],
                "explanation_text": "Explainability unavailable"
            }
            
        all_shap = self.compute_shap_values(features)
        total_var = sum(abs(v) for v in all_shap.values()) if all_shap else 1.0
        
        ranked = []
        for feat, val in top_feats:
            clean_feat = feat.replace(" (A)", "").replace(" (°C)", "").replace(" (bar)", "").replace(" (m3/h)", "").replace(" (mm/s)", "")
            impact = (val / total_var) * 100.0
            ranked.append((clean_feat, round(impact, 1)))
            
        # Build a root cause chain based on the top contributing feature
        primary_feat, primary_val = top_feats[0]
        root_cause = []
        if primary_val > 0:
            root_cause = [f"Elevated {primary_feat} detected", "AI Risk Score Increased", "Potential Degradation"]
        else:
            root_cause = [f"Normal {primary_feat}", "AI Risk Score Stabilized", "Standard Operation"]
            
        actions = []
        if ai_result.get("Plant Status") in ["WARNING", "CRITICAL"]:
            actions.append(f"Investigate {primary_feat} immediately.")
            actions.append("Check equipment physical condition.")
        else:
            actions.append("Continue standard operational monitoring.")

        return {
            "ranked_variables": ranked,
            "root_cause_chain": root_cause,
            "engineering_explanation": operator_text.replace("\n", " "),
            "recommended_actions": actions,
            "explanation_text": operator_text  # Some UI elements use this
        }
