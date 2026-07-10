"""
analytics/ai/shap_explainer.py
==============================
Phase 6 Explainable AI (XAI) Placeholder architecture.
This module will eventually use SHAP (SHapley Additive exPlanations)
to provide human-readable logic for the AI's Random Forest predictions.
"""

from typing import List, Dict, Any

class AIExplainer:
    def __init__(self, model_manager=None):
        """
        Initialize the explainer with a reference to the trained model.
        In Phase 6, this will compute SHAP values in the background.
        """
        self.model_manager = model_manager

    def explain_prediction(self, equipment_id: str, features: Dict[str, float], risk_prob: float = 0.0) -> Dict[str, Any]:
        """
        Uses SHAP to return positive and negative factors
        influencing the AI's current risk assessment, and a human readable string.
        """
        from analytics.ai.random_forest.explainability.shap_engine import SHAPEngine
        from analytics.ai.random_forest.explainability.feature_ranking import FeatureRanker
        from analytics.ai.random_forest.explainability.explanation_generator import ExplanationGenerator
        
        # In a real app we might cache the engine per equipment, but here one engine works for all
        if not hasattr(self, '_engine'):
            self._engine = SHAPEngine()
            
        shap_values = self._engine.calculate_shap(features)
        ranked = FeatureRanker.rank_features(shap_values, top_n=5)
        text = ExplanationGenerator.generate_explanation(ranked, risk_prob)
        
        # Format strings for the frontend
        def format_feature(f):
            name = ExplanationGenerator.FEATURE_MAP.get(f["feature"], f["feature"].replace('_', ' '))
            sign = "+" if f["value"] > 0 else "-"
            # We don't have exactly % risk contribution trivially, so we just format roughly
            # SHAP values are log-odds, but we can just show relative magnitude or just the sign
            return f"{name.title()} ({sign}{abs(f['value']):.2f})"

        pos_str = [format_feature(f) for f in ranked["positive_contributors"]]
        neg_str = [format_feature(f) for f in ranked["negative_contributors"]]
        
        return {
            "positive_factors": pos_str,
            "negative_factors": neg_str,
            "explanation_text": text,
            "raw_shap": shap_values,
            "ranked_features": ranked
        }
