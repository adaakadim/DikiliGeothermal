"""
analytics/decision_support/maintenance_planner.py
=================================================
Calculates estimated maintenance windows and priorities.
"""

from typing import Dict, Any

class MaintenancePlanner:
    def plan_maintenance(self, eq_id: str, fused_risk: str, rul_data: dict) -> Dict[str, str]:
        """
        Generates maintenance window suggestions based on RUL and Fused Risk.
        """
        rul_hours = rul_data.get("Remaining Useful Life (Hours)", 10000.0)
        
        # Convert hours to days roughly
        rul_days = rul_hours / 24.0
        
        if fused_risk == "CRITICAL":
            window = "Immediate Shutdown Required"
            priority = "CRITICAL"
            action = "Emergency Inspection & Bearing Replacement"
        elif fused_risk == "HIGH":
            window = f"Within {max(1, int(rul_days * 0.5))} Days"
            priority = "HIGH"
            action = "Schedule Planned Maintenance"
        elif fused_risk == "MODERATE":
            window = f"≈ {int(rul_days)} Days (Next Planned Shutdown)"
            priority = "MEDIUM"
            action = "Monitor Vibration & Motor Current"
        else:
            window = "> 3 Months"
            priority = "LOW"
            action = "Standard Routine Check"
            
        return {
            "Maintenance Priority": priority,
            "Estimated Maintenance Window": window,
            "Recommended Action": action
        }
