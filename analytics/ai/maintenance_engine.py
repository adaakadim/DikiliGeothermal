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

from dataclasses import dataclass, field
import datetime

@dataclass
class MaintenanceProfile:
    equipment_id: str
    health_score: float
    rul_days: int
    failure_probability: float
    priority: str
    recommendations: List[str]
    estimated_date: str

class PredictiveMaintenanceCenterEngine:
    def __init__(self):
        self._legacy_engine = MaintenanceEngine()
        
    def evaluate_plant_maintenance(self, readings: List[Any], ai_result: Dict[str, Any], health_indexes: Dict[str, float]) -> List[MaintenanceProfile]:
        profiles = []
        now = datetime.datetime.now()
        
        # 1. Production Pump (Uses AI)
        pump_prob = ai_result.get("Pump Failure Probability (%)", 5.0)
        pump_health = health_indexes.get("Pump Health", 95.0)
        # RUL estimation based on health
        pump_rul = max(0, int((pump_health / 100.0) * 365))
        
        legacy_rec = self._legacy_engine.get_recommendations(ai_result, health_indexes, {}, None)
        pump_priority = "LOW"
        if pump_prob > 70: pump_priority = "CRITICAL"
        elif pump_prob > 40: pump_priority = "HIGH"
        elif pump_health < 80: pump_priority = "MEDIUM"
        
        profiles.append(MaintenanceProfile(
            equipment_id="Production Pump",
            health_score=pump_health,
            rul_days=pump_rul,
            failure_probability=pump_prob,
            priority=pump_priority,
            recommendations=legacy_rec["Recommended Actions"],
            estimated_date=(now + datetime.timedelta(days=pump_rul)).strftime("%Y-%m-%d")
        ))
        
        # 2. Production Wells
        well_health = 98.0
        well_rul = 800
        well_recs = []
        for r in readings:
            if "PW" in r.well_id:
                if r.temperature_c < 80.0:
                    well_health = min(well_health, 85.0)
                    well_rul = 120
                    well_recs.append(f"Inspect production well {r.well_id} due to thermal drawdown.")
                if r.flow_m3h < 50.0:
                    well_health = min(well_health, 75.0)
                    well_rul = 60
                    well_recs.append(f"Check {r.well_id} pump alignment and casing.")
                    
        well_prob = 100.0 - well_health
        well_priority = "LOW"
        if well_health < 70: well_priority = "HIGH"
        elif well_health < 90: well_priority = "MEDIUM"
        
        if not well_recs: well_recs.append("Monitor well conditions.")
        
        profiles.append(MaintenanceProfile(
            equipment_id="Production Wells",
            health_score=well_health,
            rul_days=well_rul,
            failure_probability=well_prob,
            priority=well_priority,
            recommendations=well_recs,
            estimated_date=(now + datetime.timedelta(days=well_rul)).strftime("%Y-%m-%d")
        ))
        
        # 3. Heat Exchanger
        hx_health = health_indexes.get("Heat Exchanger Health", 92.0)
        hx_prob = max(0, 100.0 - hx_health)
        hx_rul = int((hx_health / 100.0) * 180)
        hx_priority = "LOW"
        hx_recs = []
        if hx_health < 75.0:
            hx_priority = "HIGH"
            hx_recs.append("Clean heat exchanger due to suspected fouling.")
        elif hx_health < 90.0:
            hx_priority = "MEDIUM"
            hx_recs.append("Schedule routine heat exchanger flushing.")
        else:
            hx_recs.append("Normal heat exchange efficiency.")
            
        profiles.append(MaintenanceProfile(
            equipment_id="Heat Exchanger",
            health_score=hx_health,
            rul_days=hx_rul,
            failure_probability=hx_prob,
            priority=hx_priority,
            recommendations=hx_recs,
            estimated_date=(now + datetime.timedelta(days=hx_rul)).strftime("%Y-%m-%d")
        ))
        
        # 4. Injection System
        inj_health = 96.0
        for r in readings:
            if "IW" in r.well_id:
                if r.pressure_bar > 15.0:
                    inj_health -= 15.0
                    
        inj_prob = max(0, 100.0 - inj_health)
        inj_rul = int((inj_health / 100.0) * 300)
        inj_priority = "LOW"
        inj_recs = []
        if inj_health < 85.0:
            inj_priority = "MEDIUM"
            inj_recs.append("High injection pressure detected. Calibrate sensor or inspect pipeline.")
        else:
            inj_recs.append("Injection system operating normally.")
            
        profiles.append(MaintenanceProfile(
            equipment_id="Injection System",
            health_score=inj_health,
            rul_days=inj_rul,
            failure_probability=inj_prob,
            priority=inj_priority,
            recommendations=inj_recs,
            estimated_date=(now + datetime.timedelta(days=inj_rul)).strftime("%Y-%m-%d")
        ))
        
        return profiles
