"""
analytics/ai/maintenance_engine.py
==================================
Rule-based recommendation engine for predictive maintenance.
Ingests AI output and Health indices to generate actionable advice.
"""

from typing import Dict, Any, List

class MaintenanceEngine:
    def get_recommendations(
        self, 
        ai_result: Dict[str, Any], 
        health_indexes: Dict[str, float], 
        live_features: Dict[str, Any],
        shap_res: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Returns a dictionary with maintenance advice, incorporating SHAP feature importance.
        """
        failure_prob = ai_result.get("Pump Failure Probability (%)", 0.0)
        confidence = ai_result.get("Prediction Confidence (%)", 100.0)
        
        pump_health = health_indexes.get("Pump Health", 100.0)
        motor_health = health_indexes.get("Motor Health", 100.0)
        hx_health = health_indexes.get("Heat Exchanger Health", 100.0)
        
        actions: List[str] = []
        priority = "LOW"
        status_text = "NORMAL OPERATION"
        
        # 1. Determine base risk
        if failure_prob > 70.0:
            priority = "HIGH"
            status_text = "IMMEDIATE MAINTENANCE REQUIRED"
            actions.append("Schedule emergency pump inspection.")
        elif failure_prob > 40.0:
            priority = "MEDIUM"
            status_text = "MONITORING REQUIRED"
            actions.append("Increase monitoring frequency for pump system.")
            
        # 2. XAI / SHAP-based Dynamic Actions (Phase 5.2)
        if shap_res and shap_res.get("ranked_features") and failure_prob > 30.0:
            top_pos_features = [f["feature"] for f in shap_res["ranked_features"].get("positive_contributors", [])]
            for feat in top_pos_features[:2]: # Only use top 2 to avoid spam
                if "Motor_Current" in feat:
                    actions.append(f"High motor load detected by AI: Inspect motor bearings and winding.")
                    priority = max(priority, "MEDIUM" if priority != "HIGH" else "HIGH")
                elif "Operating_Hours" in feat:
                    actions.append(f"Large operating hours contribution: Schedule preventive maintenance.")
                elif "Flow Rate_std" in feat or "Flow" in feat:
                    actions.append(f"Flow instability contribution: Inspect production well and pump impellers.")
                elif "Pressure" in feat:
                    actions.append(f"Pressure variation detected: Check pipeline blockage or filter clogging.")
                elif "Vibration" in feat:
                    actions.append(f"Vibration anomaly detected: Inspect coupling and alignment.")

        # 3. Component specific fallbacks if SHAP didn't trigger
        if motor_health < 80.0 and not any("motor" in a.lower() for a in actions):
            actions.append("Inspect motor electrical systems.")
            
        if pump_health < 80.0 and failure_prob <= 40.0 and "Flow instability" not in str(actions):
            actions.append("Check pump flow stability and cavitation risk.")
            if status_text == "NORMAL OPERATION":
                status_text = "MONITORING REQUIRED"
                
        if hx_health < 80.0:
            actions.append("Schedule heat exchanger chemical cleaning.")
            
        # 4. Confidence Safety Validation Override
        if confidence < 70.0:
            status_text = "PREDICTION UNCERTAINTY"
            actions = ["Prediction uncertainty detected.", "Collect more operating data to improve confidence."]
            priority = "LOW"
            
        if not actions:
            actions.append("Continue normal operation.")
            
        return {
            "Current Status": status_text,
            "Risk Level": priority,
            "Recommended Actions": actions,
            "Maintenance Priority": priority
        }
