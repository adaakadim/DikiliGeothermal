from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import uuid
import random

@dataclass
class Scenario:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "New Scenario"
    description: str = ""
    status: str = "STOPPED" # STOPPED, ACTIVE, PAUSED
    category: str = "CUSTOM" # DEFAULT, CUSTOM
    duration_mins: int = 60
    severity: str = "LOW" # LOW, MEDIUM, HIGH, CRITICAL
    affected_equipment: str = "ALL"
    affected_subsystem: str = "GLOBAL"
    
    start_time: Optional[datetime] = None
    last_activated: Optional[datetime] = None
    created_by: str = "Operator"

    def get_progress_pct(self) -> float:
        if self.status != "ACTIVE" or not self.start_time:
            return 0.0
        elapsed = (datetime.now() - self.start_time).total_seconds() / 60.0
        pct = (elapsed / self.duration_mins) * 100.0 if self.duration_mins > 0 else 0
        return min(100.0, max(0.0, pct))


class ScenarioManager:
    def __init__(self):
        self.scenarios: Dict[str, Scenario] = {}
        self.active_scenario: Optional[Scenario] = None
        self._load_defaults()
        
    def _load_defaults(self):
        defaults = [
            Scenario(name="Normal Operation", description="Standard baseline operation.", category="DEFAULT"),
            Scenario(name="Winter Operation", description="High district heating demand.", category="DEFAULT"),
            Scenario(name="Summer Operation", description="Low demand, reduced production.", category="DEFAULT"),
            Scenario(name="Maintenance Mode", description="System under maintenance, suppressing certain alarms.", category="DEFAULT", affected_equipment="P-101", severity="LOW"),
            Scenario(name="Pump Failure", description="Simulated degradation of pump efficiency and vibration.", category="DEFAULT", affected_equipment="P-101", severity="CRITICAL"),
            Scenario(name="Heat Exchanger Fouling", description="Gradual buildup of scale reducing efficiency.", category="DEFAULT", affected_subsystem="HX", severity="HIGH"),
            Scenario(name="Reservoir Decline", description="Slow geological cooling and pressure drop.", category="DEFAULT", affected_subsystem="RESERVOIR", severity="MEDIUM"),
            Scenario(name="Emergency Shutdown", description="Rapid isolation of wells and pump stoppage.", category="DEFAULT", severity="CRITICAL", duration_mins=15)
        ]
        for d in defaults:
            self.scenarios[d.id] = d
            
    def activate(self, scenario_id: str):
        if self.active_scenario and self.active_scenario.id != scenario_id:
            self.stop()
            
        sc = self.scenarios.get(scenario_id)
        if sc:
            sc.status = "ACTIVE"
            sc.start_time = datetime.now()
            sc.last_activated = sc.start_time
            self.active_scenario = sc
            
    def stop(self):
        if self.active_scenario:
            self.active_scenario.status = "STOPPED"
            self.active_scenario.start_time = None
            self.active_scenario = None
            
    def pause(self):
        if self.active_scenario and self.active_scenario.status == "ACTIVE":
            self.active_scenario.status = "PAUSED"
            
    def resume(self):
        if self.active_scenario and self.active_scenario.status == "PAUSED":
            self.active_scenario.status = "ACTIVE"
            
    def reset_scenario(self, scenario_id: str):
        if self.active_scenario and self.active_scenario.id == scenario_id:
            self.stop()
            self.activate(scenario_id)
            
    def delete(self, scenario_id: str):
        if scenario_id in self.scenarios and self.scenarios[scenario_id].category == "CUSTOM":
            if self.active_scenario and self.active_scenario.id == scenario_id:
                self.stop()
            del self.scenarios[scenario_id]

    def add_custom(self, sc: Scenario):
        sc.category = "CUSTOM"
        self.scenarios[sc.id] = sc

    def apply_scenario_modifiers(self, readings: List[Any], time_val: float) -> List[Any]:
        """
        Modifies SensorReadings in-place or returns a mutated copy to simulate effects.
        """
        if not self.active_scenario or self.active_scenario.status != "ACTIVE":
            return readings

        sc = self.active_scenario
        prog = sc.get_progress_pct() / 100.0 # 0.0 to 1.0

        for r in readings:
            # Base modifications
            if sc.name == "Winter Operation":
                r.flow_m3h *= 1.25 # Increase flow
                r.pressure_bar *= 1.1
            elif sc.name == "Summer Operation":
                r.flow_m3h *= 0.6 # Reduce flow
            elif sc.name == "Emergency Shutdown":
                r.flow_m3h = 0.0
                r.pressure_bar = max(1.0, r.pressure_bar * (1.0 - prog))
            elif sc.name == "Reservoir Decline":
                r.temperature_c *= (1.0 - (0.1 * prog)) # Up to 10% temp drop over duration
                r.pressure_bar *= (1.0 - (0.15 * prog))
            elif sc.name == "Pump Failure" and ("PW" in r.well_id or "P-101" in r.well_id):
                # We simulate failure by erratic flow and dropping pressure
                r.flow_m3h *= (1.0 - (0.4 * prog))
                r.pressure_bar *= (1.0 - (0.3 * prog))
            
            # Severity generic modifiers if Custom
            if sc.category == "CUSTOM":
                target_match = sc.affected_equipment == "ALL" or r.well_id == sc.affected_equipment
                if target_match:
                    factor = 1.0
                    if sc.severity == "LOW": factor = 0.95
                    elif sc.severity == "MEDIUM": factor = 0.80
                    elif sc.severity == "HIGH": factor = 0.50
                    elif sc.severity == "CRITICAL": factor = 0.10
                    
                    # Apply degradation based on progress
                    eff = 1.0 - ((1.0 - factor) * prog)
                    r.flow_m3h *= eff
                    r.pressure_bar *= eff
        return readings

    def apply_ai_modifiers(self, ai_result: Dict[str, Any]) -> Dict[str, Any]:
        """Modifies AI output dict like Pump Failure Prob based on scenario."""
        if not self.active_scenario or self.active_scenario.status != "ACTIVE":
            return ai_result
            
        sc = self.active_scenario
        prog = sc.get_progress_pct() / 100.0
        
        if sc.name == "Pump Failure" or (sc.category == "CUSTOM" and sc.severity == "CRITICAL"):
            ai_result["Pump Failure Probability (%)"] = min(99.9, ai_result.get("Pump Failure Probability (%)", 0) + (85.0 * prog))
            if prog > 0.5:
                ai_result["Plant Status"] = "CRITICAL"
                
        elif sc.name == "Heat Exchanger Fouling":
            ai_result["Equipment Health (%)"] = max(10.0, ai_result.get("Equipment Health (%)", 100) - (40.0 * prog))
            
        elif sc.name == "Emergency Shutdown":
            ai_result["Plant Status"] = "SHUTDOWN"
            ai_result["Pump Failure Probability (%)"] = 100.0
            
        return ai_result
