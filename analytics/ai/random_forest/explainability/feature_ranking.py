"""
analytics/ai/random_forest/explainability/feature_ranking.py
============================================================
Sorts and processes raw SHAP values to identify key local and global contributors.
"""

from typing import Dict, List, Any

class FeatureRanker:
    @staticmethod
    def rank_features(shap_values: Dict[str, float], top_n: int = 5) -> Dict[str, Any]:
        """
        Takes raw SHAP values for a single prediction and returns
        the top positive (risk-increasing) and negative (risk-decreasing) features.
        
        Args:
            shap_values: Dictionary of {feature_name: shap_value}
            top_n: Number of top features to return per category
            
        Returns:
            Dictionary containing:
                - 'positive_contributors': List of dicts [{"feature": name, "value": val}]
                - 'negative_contributors': List of dicts
                - 'top_overall': Combined absolute top features
        """
        if not shap_values:
            return {
                "positive_contributors": [],
                "negative_contributors": [],
                "top_overall": []
            }
            
        # Separate into positive (pushes prediction towards failure) and negative (pushes towards normal)
        positive = [{"feature": k, "value": v} for k, v in shap_values.items() if v > 0]
        negative = [{"feature": k, "value": v} for k, v in shap_values.items() if v < 0]
        
        # Sort positive by largest positive value
        positive = sorted(positive, key=lambda x: x["value"], reverse=True)
        
        # Sort negative by largest negative value (smallest mathematically)
        negative = sorted(negative, key=lambda x: x["value"])
        
        # Sort overall by absolute magnitude
        all_features = [{"feature": k, "value": v, "abs_value": abs(v)} for k, v in shap_values.items()]
        top_overall = sorted(all_features, key=lambda x: x["abs_value"], reverse=True)
        
        return {
            "positive_contributors": positive[:top_n],
            "negative_contributors": negative[:top_n],
            "top_overall": top_overall[:top_n]
        }
