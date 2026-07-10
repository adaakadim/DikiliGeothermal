"""
analytics/decision_support/decision_engine.py
=============================================
Central orchestrator for the Decision Support System.
Fuses outputs from all AI modules into unified assessments.
"""

from typing import Dict, Any, List
from .risk_fusion import RiskFusionEngine
from .maintenance_planner import MaintenancePlanner
from .recommendation_prioritizer import RecommendationPrioritizer
from .decision_history import DecisionHistory

class DecisionEngine:
    def __init__(self):
        self.risk_fusion = RiskFusionEngine()
        self.planner = MaintenancePlanner()
        self.prioritizer = RecommendationPrioritizer()
        self.history = DecisionHistory()
        
        self.assessments: Dict[str, Dict[str, Any]] = {}
        self.unified_recommendations: List[Dict[str, Any]] = []
        
        # Track previous risk states to detect changes
        self._previous_risks: Dict[str, str] = {}

    def evaluate(self, ai_result: dict, rul_results: dict, health_indexes: dict, anomaly_result: dict, opt_result: dict) -> Dict[str, Any]:
        """
        Evaluate all AI outputs and generate a unified assessment per equipment.
        """
        # We only look at primary equipment that have multiple AI outputs.
        # For DikiliGeothermal, P-101 is our main focus.
        primary_equipment = ["P-101", "GW-01", "SEP-01", "HX-101"]
        
        for eq_id in primary_equipment:
            if eq_id == "P-101":
                # For P-101 we have specific Random Forest outputs
                anom_score = anomaly_result.get("P-101 Anomaly Score", 0.0)
                rul_data = rul_results.get("P-101", {})
                health = health_indexes.get("P-101 Health", 100.0)
                
                # 1. Fuse Risk
                fused_risk = self.risk_fusion.fuse_risk(eq_id, ai_result, rul_data, health, anom_score)
                
                # 2. Plan Maintenance
                maint_plan = self.planner.plan_maintenance(eq_id, fused_risk, rul_data)
                
                # Build the unified assessment
                assessment = {
                    "Overall Risk": fused_risk,
                    "Equipment Health": f"{health:.1f}%",
                    "Remaining Useful Life": f"{rul_data.get('Remaining Useful Life (Hours)', 10000.0):.0f} Hours",
                    "Maintenance Priority": maint_plan["Maintenance Priority"],
                    "Estimated Maintenance Window": maint_plan["Estimated Maintenance Window"],
                    "Recommended Action": maint_plan["Recommended Action"],
                    "Overall AI Confidence": f"{ai_result.get('Prediction Confidence (%)', 0.0):.1f}%",
                    "Primary Root Cause": "Increasing Motor Current" if fused_risk != "LOW" else "N/A"
                }
                self.assessments[eq_id] = assessment
                
                # Log state changes
                if fused_risk != self._previous_risks.get(eq_id, "LOW"):
                    self.history.log_decision(eq_id, assessment)
                    self._previous_risks[eq_id] = fused_risk
            else:
                # Stub other equipment
                health = health_indexes.get(f"{eq_id} Health", 100.0)
                risk = "LOW" if health > 80 else ("MODERATE" if health > 50 else "HIGH")
                self.assessments[eq_id] = {
                    "Overall Risk": risk,
                    "Equipment Health": f"{health:.1f}%",
                    "Remaining Useful Life": "N/A",
                    "Maintenance Priority": risk,
                    "Estimated Maintenance Window": "> 3 Months" if risk == "LOW" else "Next Shutdown",
                    "Recommended Action": "Standard Inspection",
                    "Overall AI Confidence": "N/A",
                    "Primary Root Cause": "N/A"
                }

        # 3. Prioritize Actions
        opt_recs = opt_result.get("Recommendations", [])
        self.unified_recommendations = self.prioritizer.prioritize(opt_recs, [], self.assessments)
        
        return self.assessments
