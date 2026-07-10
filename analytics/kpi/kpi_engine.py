"""
analytics/kpi/kpi_engine.py
Central orchestrator for Plant KPIs and Operational Intelligence.
"""

from analytics.kpi.plant_health import PlantHealthCalculator
from analytics.kpi.efficiency_metrics import EfficiencyCalculator
from analytics.kpi.availability import AvailabilityCalculator
from analytics.kpi.performance_index import PerformanceIndexCalculator
from analytics.kpi.operational_intelligence import OperationalIntelligence

class KPIEngine:
    def __init__(self):
        self.health_calc = PlantHealthCalculator()
        self.efficiency_calc = EfficiencyCalculator()
        self.availability_calc = AvailabilityCalculator()
        self.performance_calc = PerformanceIndexCalculator()
        self.op_intel = OperationalIntelligence()
        
        self.history = {
            "Plant Health (%)": [],
            "Overall Efficiency (%)": [],
            "Overall AI Risk (%)": [],
            "Maintenance Readiness (%)": [],
            "Energy Production (MWh)": [],
            "Equipment Availability (%)": []
        }
        
    def evaluate(self, live_data: dict, ai_result: dict, health_indexes: dict, maint_rec: dict, rul_results: dict, opt_result: dict) -> dict:
        """
        Evaluates all sub-modules and returns a comprehensive KPI dictionary.
        """
        kpis = {}
        
        # 1. Base KPIs
        kpis.update(self.health_calc.calculate(ai_result, health_indexes, rul_results))
        kpis.update(self.efficiency_calc.calculate(live_data, opt_result))
        kpis.update(self.availability_calc.calculate(live_data, ai_result))
        kpis.update(self.performance_calc.calculate(live_data, ai_result, maint_rec))
        
        # 2. Operational Intelligence
        intel = self.op_intel.evaluate(live_data, ai_result, health_indexes, rul_results)
        kpis["Operational Intelligence"] = intel
        
        # 3. Aggregated Scores
        overall_eff = (kpis.get("Thermal Efficiency (%)", 0) * 0.5) + (kpis.get("Energy Efficiency Score (%)", 0) * 0.5)
        kpis["Overall Efficiency (%)"] = overall_eff
        
        # 4. Engineering Recommendations
        recs = []
        if kpis.get("Overall Plant Health (%)", 100) < 90:
            recs.append("Plant health is deteriorating. Schedule preventative maintenance for high-risk equipment.")
        if kpis.get("Thermal Efficiency (%)", 100) < 80:
            recs.append("Investigate decreasing thermal efficiency. Optimize heat exchanger operations.")
        if intel.get("Highest Risk Equipment") != "None":
            recs.append(f"Monitor increasing risk trend on {intel.get('Highest Risk Equipment')}.")
        if not recs:
            recs.append("All plant systems operating nominally.")
            
        kpis["Engineering Recommendations"] = recs
        
        # 5. Update History (keep last 100 points)
        self.history["Plant Health (%)"].append(kpis.get("Overall Plant Health (%)", 100))
        self.history["Overall Efficiency (%)"].append(kpis.get("Overall Efficiency (%)", 100))
        self.history["Overall AI Risk (%)"].append(kpis.get("Overall AI Risk (%)", 0))
        self.history["Maintenance Readiness (%)"].append(kpis.get("Maintenance Readiness Index (%)", 100))
        self.history["Energy Production (MWh)"].append(live_data.get("Daily Energy", 0))
        self.history["Equipment Availability (%)"].append(kpis.get("Equipment Availability (%)", 100))
        
        for key in self.history:
            if len(self.history[key]) > 100:
                self.history[key].pop(0)
                
        return kpis
