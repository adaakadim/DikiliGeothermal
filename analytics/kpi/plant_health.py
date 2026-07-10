"""
analytics/kpi/plant_health.py
Calculates overall plant health and risk metrics.
"""

class PlantHealthCalculator:
    def __init__(self):
        pass
        
    def calculate(self, ai_result: dict, health_indexes: dict, rul_results: dict) -> dict:
        """
        Calculates plant-level health and risk.
        """
        kpis = {}
        
        # 1. Overall Plant Health
        kpis["Overall Plant Health (%)"] = health_indexes.get("Overall Plant Health", 100.0)
        
        # 2. Overall AI Risk
        # We can take the max risk or a weighted average of risks from AI result
        overall_risk = ai_result.get("Pump Failure Probability (%)", 0.0)
        # If we had multiple pumps predicted, we could average or max them here.
        kpis["Overall AI Risk (%)"] = overall_risk
        
        # 3. Average Equipment Health
        eq_healths = []
        for eq_id, rul_data in rul_results.items():
            if "P-" in eq_id or "GW-" in eq_id or "HX-" in eq_id or "SEP-" in eq_id:
                # Assuming RUL results or health_indexes has individual healths.
                # In current implementation, pump health is under 'Pump Health' in health_indexes
                pass
                
        # Since health_indexes currently provides Pump Health, we'll use it
        pump_health = health_indexes.get("Pump Health", 100.0)
        
        # For a robust calculation, we average the plant health and pump health
        kpis["Average Equipment Health (%)"] = (kpis["Overall Plant Health (%)"] + pump_health) / 2.0
        
        # 4. Average Remaining Useful Life (Hours)
        rul_values = [d.get("Remaining Useful Life (Hours)", 0) for d in rul_results.values() if d.get("Remaining Useful Life (Hours)", 0) > 0]
        if rul_values:
            kpis["Average Remaining Useful Life (Hours)"] = sum(rul_values) / len(rul_values)
        else:
            kpis["Average Remaining Useful Life (Hours)"] = 50000.0 # Default high value
            
        # 5. Average Failure Probability
        kpis["Average Failure Probability (%)"] = overall_risk * 0.8 # Simplified weighted risk
        
        return kpis
