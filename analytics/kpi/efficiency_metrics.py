"""
analytics/kpi/efficiency_metrics.py
Calculates plant efficiency KPIs.
"""

class EfficiencyCalculator:
    def __init__(self):
        pass
        
    def calculate(self, live_data: dict, opt_result: dict) -> dict:
        kpis = {}
        
        # 1. Thermal Efficiency
        hx_eff = live_data.get("Heat Exchanger Efficiency", 0.0)
        kpis["Thermal Efficiency (%)"] = hx_eff
        
        # 2. Energy Efficiency Score
        # Can be derived from Plant Load and Efficiency
        plant_load = live_data.get("Plant Load", 70.0)
        kpis["Energy Efficiency Score (%)"] = (hx_eff * 0.7) + (plant_load * 0.3)
        
        # 3. Heat Recovery Efficiency
        # Delta T across the network compared to optimal
        dt = live_data.get("District Heating Supply Temperature", 80.0) - live_data.get("District Heating Return Temperature", 60.0)
        optimal_dt = 20.0
        hr_eff = min(100.0, max(0.0, (dt / optimal_dt) * 100.0))
        kpis["Heat Recovery Efficiency (%)"] = hr_eff
        
        return kpis
