from enum import Enum
from typing import Optional

class PlantMode(Enum):
    NORMAL = "NORMAL"
    WINTER_PEAK = "WINTER_PEAK"
    SUMMER_MODE = "SUMMER_MODE"
    MAINTENANCE = "MAINTENANCE"
    PUMP_FAILURE = "PUMP_FAILURE"
    HX_FOULING = "HX_FOULING"
    RESERVOIR_DECLINE = "RESERVOIR_DECLINE"
    EMERGENCY_SHUTDOWN = "EMERGENCY_SHUTDOWN"

class ModeManager:
    """Manages plant simulation modes and overriding multipliers/targets."""
    
    def __init__(self):
        self.current_mode: PlantMode = PlantMode.NORMAL
        self.target_equipment: Optional[str] = None
        self._reservoir_decline_factor: float = 1.0

    def set_mode(self, mode: PlantMode, target: str = None):
        self.current_mode = mode
        self.target_equipment = target

    def get_load_factor_override(self, base_load: float) -> float:
        """Overrides the dynamic diurnal demand load factor based on the active mode."""
        if self.current_mode == PlantMode.WINTER_PEAK:
            return 0.85 + (base_load - 0.40) * 1.2
        elif self.current_mode == PlantMode.SUMMER_MODE:
            return 0.20 + (base_load - 0.40) * 0.5
        elif self.current_mode == PlantMode.EMERGENCY_SHUTDOWN:
            return 0.0
        return base_load

    def get_flow_target(self, equipment_id: str, default_target: float) -> float:
        """Determines flow targets, handling maintenance and emergency stops."""
        if self.current_mode == PlantMode.EMERGENCY_SHUTDOWN:
            return 0.0
        if self.current_mode == PlantMode.MAINTENANCE and equipment_id == self.target_equipment:
            return 0.0
        if self.current_mode == PlantMode.RESERVOIR_DECLINE:
            return default_target * self._reservoir_decline_factor
        return default_target

    def get_reservoir_temp_override(self, default_temp: float) -> float:
        """Simulates long-term geological cooling."""
        if self.current_mode == PlantMode.RESERVOIR_DECLINE:
            # Gradually reduce decline factor
            self._reservoir_decline_factor = max(0.6, self._reservoir_decline_factor - 0.0001)
            return default_temp * self._reservoir_decline_factor
        return default_temp

    def get_pump_wear_rate(self, equipment_id: str, default_rate: float) -> float:
        """Accelerates wear during pump failure mode."""
        if self.current_mode == PlantMode.PUMP_FAILURE and equipment_id == self.target_equipment:
            return default_rate * 10000.0  # Spike wear significantly
        return default_rate

    def get_hx_fouling_rate(self, default_rate: float) -> float:
        """Accelerates fouling during fouling mode."""
        if self.current_mode == PlantMode.HX_FOULING:
            return default_rate * 1000.0  # Rapid scaling
        return default_rate
