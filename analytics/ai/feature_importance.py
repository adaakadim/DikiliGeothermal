"""
analytics/ai/feature_analysis.py
================================
Extracts real-time feature importance and generates human-readable
AI decision explanations from the active Random Forest memory cache.
"""

from typing import List, Dict, Any, Tuple
from analytics.ai.random_forest.model_loader import ModelCache

class FeatureAnalyzer:
    def __init__(self):
        # We cache the sorted features so we don't recalculate them on every tick
        self._cached_importances: List[Tuple[str, float]] = []
        
    def _extract_importances(self):
        """Loads the active pump failure model and extracts feature weights."""
        model = ModelCache.get_model("PumpFailure_RF")
        if not model:
            return
            
        if hasattr(model, "feature_importances_") and hasattr(model, "feature_names_in_"):
            weights = model.feature_importances_
            names = model.feature_names_in_
            
            # Combine and sort descending
            combined = sorted(zip(names, weights), key=lambda x: x[1], reverse=True)
            self._cached_importances = combined
            
    def get_top_features(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """Returns the top N most important features driving the AI."""
        if not self._cached_importances:
            self._extract_importances()
            
        return [
            {"name": name, "weight": round(weight * 100.0, 1)}
            for name, weight in self._cached_importances[:top_n]
        ]
        
    def generate_explanation(self, live_features: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Generates a basic text explanation based on the top features and their current live values.
        """
        top_features = self.get_top_features(top_n=3)
        
        increasing_factors = []
        normal_factors = []
        
        for f in top_features:
            name = f["name"]
            val = live_features.get(name, 0.0)
            
            # Very basic anomaly heuristic for text explanation
            # In a real system, this would use SHAP baseline comparisons
            if "Current" in name and val > 65:
                increasing_factors.append(f"High {name.lower()} detected ({val:.1f})")
            elif "Flow" in name and val < 90:
                increasing_factors.append(f"Low {name.lower()} detected ({val:.1f})")
            elif "Pressure" in name and val < 4.0:
                increasing_factors.append(f"Pressure drop detected ({val:.1f})")
            elif "Temperature" in name and val > 105:
                increasing_factors.append(f"Excessive {name.lower()} ({val:.1f})")
            else:
                normal_factors.append(f"{name} is stable ({val:.1f})")
                
        if not increasing_factors:
            increasing_factors.append("No immediate active risk drivers")
            
        return {
            "increasing": increasing_factors,
            "normal": normal_factors
        }
