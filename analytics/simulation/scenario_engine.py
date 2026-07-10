"""
analytics/simulation/scenario_engine.py
=======================================
Isolated simulation environment that applies user overrides to live data
and runs them through existing AI models to predict future states.
"""

from typing import Dict, Any
import copy
import logging

from analytics.ai.random_forest.predictor import predict_plant_state
from analytics.ai.health_index import HealthIndexEngine
from analytics.ai.rul.rul_engine import RULEngine
from analytics.ai.feature_engineering import FeatureEngineer

logger = logging.getLogger(__name__)

class ScenarioEngine:
    def __init__(self):
        self._feature_engineer = FeatureEngineer(window_size=1) # Single-shot evaluation
        self._health_engine = HealthIndexEngine()
        self._rul_engine = RULEngine(update_interval_hours=0.0) # Used statically
        
        self.last_simulated_state: Dict[str, Any] = {}
        self.last_simulated_ai: Dict[str, Any] = {}
        
    def run_simulation(self, live_data: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes the base live data, applies overrides, runs it through AI models.
        """
        # Create an isolated copy
        sim_data = copy.deepcopy(live_data)
        
        # Apply user overrides
        for k, v in overrides.items():
            if k in sim_data:
                sim_data[k] = v
                
        # Re-calculate dependent thermodynamics within the simulation
        if "Flow Rate (m3/h)" in overrides:
            flow = overrides["Flow Rate (m3/h)"]
            sim_data["Motor Current (A)"] = flow * 0.45
            sim_data["Motor Power (kW)"] = (flow * 0.45 * 400.0 * 1.732 * 0.85 / 1000.0)
            
            hx_eff = sim_data.get("Heat Exchanger Efficiency", 85.0)
            sim_data["Thermal Power (MW)"] = flow * 4.186 * 15.0 / 3600 / 1000
            
        if "Heat Exchanger Efficiency" in overrides:
            hx_eff = overrides["Heat Exchanger Efficiency"]
            avg_temp = sim_data.get("Temperature (°C)", 100.0)
            sim_data["Heat Exchanger Outlet Temperature"] = avg_temp - (avg_temp * hx_eff / 100.0 * 0.2)
            
        self.last_simulated_state = sim_data

        # 1. Feature Engineering (Single Shot)
        engineered_data = self._feature_engineer.process_row(sim_data)
        
        # 2. Random Forest Inference
        ai_result = predict_plant_state(engineered_data, lifecycle_engine=None)
        
        # 3. Health Index
        health_indexes = self._health_engine.calculate_indexes(sim_data, ai_result)
        health = health_indexes.get("Pump Health", 100.0)
        
        # 4. RUL Estimation
        rul_data = self._rul_engine.estimate_rul("P-101", sim_data, ai_result, health)
        
        self.last_simulated_ai = {
            "Plant Status": ai_result["Plant Status"],
            "Pump Failure Probability (%)": ai_result["Pump Failure Probability (%)"],
            "Equipment Health (%)": health,
            "Remaining Useful Life (Hours)": rul_data.get("Remaining Useful Life (Hours)", 10000.0),
            "Thermal Power (MW)": sim_data.get("Thermal Power (MW)", 0.0)
        }
        
        return self.last_simulated_ai
