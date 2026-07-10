"""
analytics/simulation/impact_estimator.py
========================================
Compares live data with simulated data and generates engineering recommendations.
"""

from typing import Dict, Any

class ImpactEstimator:
    def estimate_impact(self, live_ai: Dict[str, Any], sim_ai: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates the deltas between live and simulated states.
        """
        base_risk = live_ai.get("Pump Failure Probability (%)", 0.0)
        sim_risk = sim_ai.get("Pump Failure Probability (%)", 0.0)
        risk_delta = sim_risk - base_risk
        
        base_health = live_ai.get("Equipment Health (%)", 100.0)
        sim_health = sim_ai.get("Equipment Health (%)", 100.0)
        health_delta = sim_health - base_health
        
        base_rul = live_ai.get("Remaining Useful Life (Hours)", 10000.0)
        sim_rul = sim_ai.get("Remaining Useful Life (Hours)", 10000.0)
        rul_delta = sim_rul - base_rul
        
        base_power = live_ai.get("Thermal Power (MW)", 0.0)
        sim_power = sim_ai.get("Thermal Power (MW)", 0.0)
        power_delta = sim_power - base_power
        
        # Generate recommendation
        rec = "The proposed changes have a minimal impact on overall plant operations."
        
        if risk_delta < -10.0:
            rec = f"Operating under the proposed scenario significantly reduces failure probability by {abs(risk_delta):.1f}%. Recommended."
        elif risk_delta > 10.0:
            rec = f"WARNING: The proposed scenario increases pump failure risk by {risk_delta:.1f}%. Avoid if possible."
        elif power_delta > 0.5 and risk_delta < 5.0:
            rec = f"Excellent! The proposed scenario increases thermal output by {power_delta:.2f} MW without significant risk."
        elif rul_delta > 100:
            rec = f"Operating under the proposed scenario extends the Remaining Useful Life of the pump."
            
        return {
            "Failure Risk Delta": risk_delta,
            "Health Delta": health_delta,
            "RUL Delta": rul_delta,
            "Power Delta": power_delta,
            "Recommendation": rec
        }
