"""
analytics/ai/rul/rul_engine.py
==============================
Main engine for estimating Remaining Useful Life (RUL).
Combines health decay, degradation models, and maintenance scheduling.
"""

from typing import Dict, Any
from .health_decay import HealthDecayModel
from .degradation_model import EquipmentDegradationModel
from .maintenance_scheduler import MaintenanceScheduler
from .rul_history import RULHistoryManager

class RULEngine:
    def __init__(self, update_interval_hours: float = 0.01):
        self.health_decay = HealthDecayModel(nominal_life_hours=10000.0)
        self.degradation_model = EquipmentDegradationModel()
        self.scheduler = MaintenanceScheduler()
        self.history = RULHistoryManager()
        
        # Keep track of current RUL for each equipment
        self._rul_state: Dict[str, float] = {}
        # How much real time / simulation time passes per tick (e.g. 1 hour simulated per tick)
        self.update_interval_hours = update_interval_hours
        
    def estimate_rul(self, eq_id: str, live_data: Dict[str, Any], ai_result: Dict[str, Any], health_index: float) -> Dict[str, Any]:
        """
        Estimate the Remaining Useful Life for a specific equipment.
        
        Parameters:
            eq_id (str): Equipment identifier (e.g. "P-101")
            live_data (dict): Telemetry parameters
            ai_result (dict): Outputs from predictive models (Failure Probability)
            health_index (float): Output from Health Index Engine (0-100)
        """
        
        # Initialize if not exists
        if eq_id not in self._rul_state:
            # We start with the nominal life modified by current health
            self._rul_state[eq_id] = self.health_decay.nominal_life_hours * (health_index / 100.0)
            
        current_rul = self._rul_state[eq_id]
        failure_prob = ai_result.get("Pump Failure Probability (%)", 0.0)
        
        # 1. Calculate decay rate
        decay_rate = self.health_decay.calculate_decay_rate(failure_prob, health_index)
        
        # 2. Apply decay
        # Decrease RUL by the base interval multiplied by the decay rate
        current_rul -= (self.update_interval_hours * decay_rate)
        
        # Ensure it doesn't drop below 0
        current_rul = max(0.0, current_rul)
        self._rul_state[eq_id] = current_rul
        
        # 3. Assess Degradation
        degradation = self.degradation_model.evaluate(live_data, health_index, current_rul)
        
        # 4. Schedule Maintenance
        maint_info = self.scheduler.categorize(current_rul)
        
        # 5. Calculate Confidence
        base_confidence = 100.0 - (failure_prob * 0.5)
        # Confidence drops as RUL approaches 0
        if current_rul < 500:
            base_confidence *= 0.8
            
        # 6. Record History
        self.history.add_record(eq_id, current_rul, health_index, failure_prob)
            
        return {
            "Equipment": eq_id,
            "Remaining Useful Life (Hours)": current_rul,
            "Estimated Remaining Days": current_rul / 24.0,
            "Current Degradation": degradation,
            "Degradation Rate": decay_rate,
            "Confidence (%)": min(100.0, max(0.0, base_confidence)),
            "Maintenance Status": maint_info["Status"],
            "Maintenance Priority": maint_info["Priority"]
        }
