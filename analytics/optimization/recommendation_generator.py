"""
analytics/optimization/recommendation_generator.py
==================================================
Rule-based expert system generating actionable engineering recommendations 
for process optimization based on calculated efficiencies and AI predictions.
"""

from typing import Dict, Any, List

class RecommendationGenerator:
    def __init__(self):
        pass
        
    def generate(self, kpis: Dict[str, float], ai_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evaluate KPIs and AI risk to generate specific recommendations.
        Returns a list of dictionaries with optimization suggestions.
        """
        recommendations = []
        
        hx_eff = kpis.get("Heat Exchanger Efficiency (%)", 100.0)
        pump_eff = kpis.get("Pump Efficiency (%)", 100.0)
        plant_load = kpis.get("Plant Load (%)", 100.0)
        failure_prob = ai_results.get("Pump Failure Probability (%)", 0.0)
        
        # Rule 1: Heat Exchanger Fouling
        if hx_eff < 85.0:
            est_imp = min(15.0, 95.0 - hx_eff)
            recommendations.append({
                "Equipment": "HX-101",
                "Efficiency": hx_eff,
                "Target Efficiency": 93.0,
                "Suggestion": "Investigate heat exchanger fouling due to declining thermal transfer.",
                "Estimated Improvement": f"+{est_imp:.1f}%",
                "Priority": "High" if hx_eff < 75 else "Medium"
            })
            
        # Rule 2: Pump Overload / Inefficiency
        if pump_eff < 75.0 and failure_prob > 40.0:
            est_imp = min(10.0, 85.0 - pump_eff)
            recommendations.append({
                "Equipment": "P-101",
                "Efficiency": pump_eff,
                "Target Efficiency": 82.0,
                "Suggestion": "Inspect pump bearings; increasing motor current is reducing efficiency.",
                "Estimated Improvement": f"+{est_imp:.1f}%",
                "Priority": "High"
            })
        elif pump_eff < 70.0:
            est_imp = min(15.0, 85.0 - pump_eff)
            recommendations.append({
                "Equipment": "P-101",
                "Efficiency": pump_eff,
                "Target Efficiency": 82.0,
                "Suggestion": "Reduce pump speed by a small percentage to improve hydraulic efficiency.",
                "Estimated Improvement": f"+{est_imp:.1f}%",
                "Priority": "Medium"
            })
            
        # Rule 3: High Plant Load Balancing
        if plant_load > 95.0 and hx_eff < 90.0:
            recommendations.append({
                "Equipment": "DH-NET",
                "Efficiency": plant_load,
                "Target Efficiency": 90.0,
                "Suggestion": "Balance flow rate between production and district heating circuits to reduce thermal stress.",
                "Estimated Improvement": "+5.0% Thermal Cap",
                "Priority": "Medium"
            })
            
        # Rule 4: Preventative Maintenance for Efficiency
        if failure_prob > 75.0:
            recommendations.append({
                "Equipment": "GW-01 System",
                "Efficiency": kpis.get("Overall Plant Efficiency (%)", 0.0),
                "Target Efficiency": 90.0,
                "Suggestion": "Schedule maintenance before efficiency loss becomes critical.",
                "Estimated Improvement": "Risk Mitigated",
                "Priority": "Critical"
            })
            
        return recommendations
