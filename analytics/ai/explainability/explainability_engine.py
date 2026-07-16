from abc import ABC, abstractmethod
from typing import Dict, Any, List
import operator

class BaseExplainer(ABC):
    """
    Abstract Base Class for the AI Explainability Engine.
    Designed so that a future SHAP-based engine can drop in.
    """
    @abstractmethod
    def generate_explanation(self, target_id: str, features: Dict[str, float], ai_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates an explanation for a given prediction.
        Must return a dictionary containing:
        - 'ranked_variables': list of tuples (variable_name, relative_impact_score)
        - 'root_cause_chain': list of strings
        - 'engineering_explanation': str
        - 'recommended_actions': list of strings
        """
        pass

class HeuristicExplainer(BaseExplainer):
    """
    Internal explainability engine that uses thermodynamics heuristics
    to explain AI predictions based on live feature values.
    """
    
    # Simple thresholds for heuristics (in a real system, drawn from Engineering Profiles)
    THRESHOLDS = {
        "Motor Current (A)": {"high": 120.0, "low": 20.0},
        "Motor Voltage (V)": {"high": 420.0, "low": 380.0},
        "Temperature (°C)": {"high": 110.0, "low": 70.0},
        "Pressure (bar)": {"high": 12.0, "low": 4.0},
        "Flow Rate (m3/h)": {"high": 250.0, "low": 50.0},
        "Feature_Flow_Stability_Index": {"high": 10.0, "low": 0.0},
    }

    def generate_explanation(self, target_id: str, features: Dict[str, float], ai_result: Dict[str, Any]) -> Dict[str, Any]:
        ranked = []
        root_cause_chain = []
        explanation_sentences = []
        actions = []
        
        # 1. Rank contributing variables based on deviation from 'normal' (heuristic)
        deviations = {}
        for feat, val in features.items():
            if feat in self.THRESHOLDS:
                th = self.THRESHOLDS[feat]
                mid = (th["high"] + th["low"]) / 2.0
                range_span = th["high"] - th["low"]
                # Normalize deviation: how far from midpoint relative to the span
                dev = abs(val - mid) / (range_span if range_span > 0 else 1)
                deviations[feat] = dev
        
        # Sort by deviation descending
        ranked = sorted(deviations.items(), key=operator.itemgetter(1), reverse=True)
        # Format for UI (just taking top 5)
        ranked = [(feat, round(dev * 100, 1)) for feat, dev in ranked[:5]]
        
        # 2. Build Root Cause Chain & Explanation based on highest deviated features
        if ranked:
            top_feat, _ = ranked[0]
            val = features.get(top_feat, 0.0)
            
            if top_feat == "Motor Current (A)" and val > self.THRESHOLDS[top_feat]["high"]:
                root_cause_chain = ["High Motor Current", "Excessive Pump Load", "Impending Bearing Overload", "Potential Pump Failure"]
                explanation_sentences.append("The AI detected an abnormally high motor current drawn by the pump.")
                explanation_sentences.append("This is typically caused by increased mechanical friction or hydraulic resistance.")
                explanation_sentences.append("If left unchecked, this condition leads to bearing degradation and imminent pump failure.")
                actions = ["Monitor vibration levels on pump bearings.", "Inspect pump alignment.", "Check for blockages in the production line."]
            
            elif top_feat == "Feature_Flow_Stability_Index" and val > self.THRESHOLDS[top_feat]["high"]:
                root_cause_chain = ["Unstable Flow Profile", "Cavitation", "Impeller Damage", "Pump Degradation"]
                explanation_sentences.append("The flow stability index indicates severe fluctuations in production flow.")
                explanation_sentences.append("Such instability often induces cavitation, where vapor bubbles form and collapse violently.")
                explanation_sentences.append("This causes pitting on the impeller and accelerated mechanical wear.")
                actions = ["Throttle pump discharge to stabilize flow.", "Verify wellhead pressure is sufficient.", "Check separator fluid level."]
                
            elif top_feat == "Temperature (°C)" and val < self.THRESHOLDS[top_feat]["low"]:
                root_cause_chain = ["Thermal Drawdown", "Decreased Enthalpy", "Reduced Thermal Output", "System Underperformance"]
                explanation_sentences.append("Production fluid temperature has dropped significantly below expected operational bounds.")
                explanation_sentences.append("This thermal drawdown reduces the available enthalpy for the heat exchanger.")
                explanation_sentences.append("Consequently, the district heating network may experience reduced supply temperatures.")
                actions = ["Reduce production flow to allow reservoir thermal recovery.", "Optimize heat exchanger bypass.", "Evaluate well scaling."]
            
            else:
                root_cause_chain = [f"Deviation in {top_feat}", "Sub-optimal Operation", "Decreased Health"]
                explanation_sentences.append(f"The parameter {top_feat} is currently evaluating at {val:.1f}.")
                explanation_sentences.append("This deviation is contributing heavily to the AI's current risk assessment.")
                actions = [f"Investigate {top_feat} sensor reading.", "Review recent operational setpoint changes.", "Check equipment calibration."]
        else:
            root_cause_chain = ["Normal Operation", "Stable State"]
            explanation_sentences.append("All primary parameters are operating within expected boundaries.")
            actions = ["Continue normal monitoring."]
            
        # Compile response
        return {
            "ranked_variables": ranked,
            "root_cause_chain": root_cause_chain,
            "engineering_explanation": " ".join(explanation_sentences),
            "recommended_actions": actions
        }
