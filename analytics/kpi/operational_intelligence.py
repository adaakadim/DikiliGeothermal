"""
analytics/kpi/operational_intelligence.py
Identifies critical extremes in operations.
"""

class OperationalIntelligence:
    def __init__(self):
        pass
        
    def evaluate(self, live_data: dict, ai_result: dict, health_indexes: dict, rul_results: dict) -> dict:
        intel = {}
        
        # In a real system, we'd loop over all equipment. 
        # Here we use the summarized data to pinpoint the most critical ones.
        
        # Highest Risk
        overall_risk = ai_result.get("Pump Failure Probability (%)", 0.0)
        if overall_risk > 70:
            intel["Highest Risk Equipment"] = "P-101 (Production Pump)"
        elif overall_risk > 40:
            intel["Highest Risk Equipment"] = "P-101 (Production Pump)"
        else:
            intel["Highest Risk Equipment"] = "None"
            
        # Lowest Health
        pump_health = health_indexes.get("Pump Health", 100.0)
        plant_health = health_indexes.get("Overall Plant Health", 100.0)
        
        if pump_health < plant_health:
            intel["Lowest Health Equipment"] = f"P-101 ({pump_health:.1f}%)"
        else:
            intel["Lowest Health Equipment"] = f"General Plant ({plant_health:.1f}%)"
            
        # Lowest Efficiency
        hx_eff = live_data.get("Heat Exchanger Efficiency", 100.0)
        if hx_eff < 75.0:
            intel["Lowest Efficiency Equipment"] = f"HX-101 ({hx_eff:.1f}%)"
        else:
            intel["Lowest Efficiency Equipment"] = "Optimal"
            
        # Fastest Degrading
        fastest_deg = "None"
        max_deg_rate = 0.0
        for eq_id, rul_data in rul_results.items():
            deg_rate = rul_data.get("Degradation Rate", 0.0)
            if deg_rate > max_deg_rate:
                max_deg_rate = deg_rate
                fastest_deg = eq_id
                
        intel["Fastest Degrading Equipment"] = fastest_deg if max_deg_rate > 0.01 else "None"
        
        # Most Frequent Alarm Source
        alarm_count = live_data.get("Alarm Count", 0)
        if alarm_count > 0:
            intel["Most Frequent Alarm Source"] = "P-101 / High Risk"
        else:
            intel["Most Frequent Alarm Source"] = "None"
            
        # Immediate Maintenance
        if overall_risk > 75:
            intel["Equipment Requiring Immediate Maintenance"] = "P-101"
        else:
            intel["Equipment Requiring Immediate Maintenance"] = "None"
            
        return intel
