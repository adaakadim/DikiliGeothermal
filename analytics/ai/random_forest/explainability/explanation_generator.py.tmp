"""
analytics/ai/random_forest/explainability/explanation_generator.py
==================================================================
Translates SHAP feature rankings into human-readable engineering explanations.
"""

from typing import Dict, Any

class ExplanationGenerator:
    
    # Mapping raw feature names to human readable strings
    FEATURE_MAP = {
        "Flow Rate_mean": "flow rate",
        "Temperature_mean": "temperature",
        "Pressure_mean": "pressure",
        "Flow Rate_std": "flow instability",
        "Temperature_std": "temperature fluctuation",
        "Pressure_std": "pressure fluctuation",
        "Pump_Operating_Hours": "accumulated operating hours",
        "Motor_Current_mean": "motor current",
        "Motor_Current_std": "motor load instability",
        "Vibration_Level": "vibration"
    }

    @classmethod
    def generate_explanation(cls, ranked_features: Dict[str, Any], risk_prob: float) -> str:
        """
        Generate a human-readable explanation of why the model predicted the current risk.
        """
        pos = ranked_features.get("positive_contributors", [])
        neg = ranked_features.get("negative_contributors", [])
        
        if not pos and not neg:
            return "No explanation data available."

        # High risk explanation
        if risk_prob > 50.0:
            if not pos:
                return "The predicted risk is elevated due to a combination of minor factors."
            
            top_pos = [cls.FEATURE_MAP.get(f["feature"], f["feature"].replace('_', ' ').lower()) for f in pos[:2]]
            
            if len(top_pos) == 1:
                return f"The predicted risk increased primarily because the {top_pos[0]} is abnormal."
            else:
                return f"The prediction is driven by elevated {top_pos[0]} combined with {top_pos[1]}."
        
        # Low risk explanation
        else:
            if not neg:
                return "The equipment remains healthy."
                
            top_neg = [cls.FEATURE_MAP.get(f["feature"], f["feature"].replace('_', ' ').lower()) for f in neg[:2]]
            
            if len(top_neg) == 1:
                return f"The equipment remains healthy because {top_neg[0]} is within expected operating conditions."
            else:
                return f"The equipment is stable, supported by normal {top_neg[0]} and {top_neg[1]}."
