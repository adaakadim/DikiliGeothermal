"""
analytics/optimization/optimization_engine.py
=============================================
Orchestrates the optimization process by connecting the Efficiency Analyzer,
Recommendation Generator, and Optimization History modules.
"""

from typing import Dict, Any, List
from .efficiency_analyzer import EfficiencyAnalyzer
from .recommendation_generator import RecommendationGenerator
from .optimization_history import OptimizationHistoryManager

class OptimizationEngine:
    def __init__(self):
        self.analyzer = EfficiencyAnalyzer()
        self.generator = RecommendationGenerator()
        self.history = OptimizationHistoryManager()
        
    def evaluate(self, live_data: Dict[str, Any], ai_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate plant performance and generate optimization insights.
        """
        # 1. Calculate physics-based efficiencies and KPIs
        kpis = self.analyzer.analyze(live_data)
        
        # 2. Track history
        self.history.add_record(kpis)
        
        # 3. Generate actionable recommendations
        recommendations = self.generator.generate(kpis, ai_results)
        
        # Map lowest efficiency equipment
        lowest_eff_eq = "None"
        lowest_eff_val = 100.0
        
        pump_eff = kpis.get("Pump Efficiency (%)", 100.0)
        hx_eff = kpis.get("Heat Exchanger Efficiency (%)", 100.0)
        
        if pump_eff < hx_eff:
            lowest_eff_eq = "P-101 (Pump)"
            lowest_eff_val = pump_eff
        else:
            lowest_eff_eq = "HX-101 (Heat Exchanger)"
            lowest_eff_val = hx_eff
            
        return {
            "KPIs": kpis,
            "Recommendations": recommendations,
            "Lowest Efficiency Equipment": f"{lowest_eff_eq} ({lowest_eff_val:.1f}%)"
        }
