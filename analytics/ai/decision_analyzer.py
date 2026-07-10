"""
analytics/ai/decision_analyzer.py
=================================
Rule-based analyzer for AI decisions. Compares consecutive predictions and 
generates human-readable engineering explanations for shifts in risk.
Does NOT use SHAP.
"""

from typing import Dict, Any

class DecisionAnalyzer:
    _previous_features = {}
    _previous_prediction = {}

    @classmethod
    def analyze_decision(cls, current_features: Dict[str, Any], current_prediction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes the delta between current and previous state to generate rule-based explanations.
        """
        event = cls.compare_decisions(
            cls._previous_prediction, current_prediction,
            cls._previous_features, current_features
        )
        
        # Cache for next cycle
        cls._previous_prediction = dict(current_prediction)
        cls._previous_features = dict(current_features)
        
        return event

    @classmethod
    def compare_decisions(cls, prev_prediction: Dict[str, Any], curr_prediction: Dict[str, Any],
                          prev_features: Dict[str, Any], curr_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compares any two predictions (prev and curr) and their features to generate deltas and explanations.
        If prev_prediction is empty, treats it as the first cycle.
        """
        timestamp = curr_prediction.get("Prediction Timestamp", curr_prediction.get("time", ""))
        equipment = curr_prediction.get("Equipment Name", curr_prediction.get("equipment", "PLANT"))
        
        # Current state
        c_fail = curr_prediction.get("Pump Failure Probability (%)", curr_prediction.get("failure_probability", 0.0))
        c_health = curr_prediction.get("Equipment Health (%)", curr_prediction.get("health_score", 100.0))
        c_conf = curr_prediction.get("Prediction Confidence (%)", curr_prediction.get("confidence", 0.0))
        
        # Previous state
        p_fail = prev_prediction.get("Pump Failure Probability (%)", prev_prediction.get("failure_probability", c_fail))
        p_health = prev_prediction.get("Equipment Health (%)", prev_prediction.get("health_score", c_health))
        p_conf = prev_prediction.get("Prediction Confidence (%)", prev_prediction.get("confidence", c_conf))
        
        # Deltas
        risk_delta = c_fail - p_fail
        health_delta = c_health - p_health
        conf_delta = c_conf - p_conf
        
        # Sensor Changes
        sensor_changes = []
        explanation_triggers = []
        
        if prev_features:
            for feat, c_val in curr_features.items():
                p_val = prev_features.get(feat, c_val)
                if isinstance(c_val, (int, float)) and isinstance(p_val, (int, float)):
                    # Calculate percentage change if base > 0 to avoid division by zero
                    diff = c_val - p_val
                    pct_change = (abs(diff) / max(abs(p_val), 1.0)) * 100.0
                    
                    if pct_change > 1.0: # Meaningful deviation threshold
                        sensor_changes.append({
                            "feature": feat,
                            "old": round(p_val, 2),
                            "new": round(c_val, 2),
                            "diff": round(diff, 2),
                            "pct": round(pct_change, 1)
                        })
                        
                        # Apply rule-based heuristics for explanation text
                        if "Current" in feat and diff > 5.0 and risk_delta > 1.0:
                            explanation_triggers.append(f"Motor current increased by {pct_change:.1f}% causing elevated failure risk.")
                        if "Pressure" in feat and diff < -0.5 and risk_delta > 1.0:
                            explanation_triggers.append("Pressure drop detected.")
                        if "Flow" in feat and diff < -5.0 and risk_delta > 1.0:
                            explanation_triggers.append("Flow rate reduction compared to previous cycle.")
                        if "Efficiency" in feat and diff < -2.0:
                            explanation_triggers.append("Thermal efficiency degraded.")
                            
        # Formulate Explanation
        if not explanation_triggers:
            if abs(risk_delta) < 1.0:
                reason = "System operating steadily. No significant deviations."
            elif risk_delta > 0:
                reason = "Minor cumulative sensor drift resulting in slight risk elevation."
            else:
                reason = "Conditions stabilized. Risk profile decreased."
        else:
            reason = " ".join(explanation_triggers)

        # Build output Event
        event = {
            "timestamp": timestamp,
            "equipment": equipment,
            "prediction": curr_prediction,
            "deltas": {
                "risk": round(risk_delta, 2),
                "health": round(health_delta, 2),
                "confidence": round(conf_delta, 2)
            },
            "sensor_changes": sensor_changes,
            "reason_summary": reason,
            "raw_features": curr_features
        }
        
        return event
