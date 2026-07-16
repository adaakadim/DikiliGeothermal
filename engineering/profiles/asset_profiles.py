from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

@dataclass
class LimitRange:
    """Defines min and max boundaries for a given operating state."""
    min_val: float
    max_val: float

    def contains(self, value: float) -> bool:
        return self.min_val <= value <= self.max_val

@dataclass
class EngineeringProfile:
    """Centralized Engineering Profile defining operating envelopes and alarm limits."""
    equipment_type: str
    
    # Core operating parameters
    temperature_limits: Dict[str, LimitRange] = field(default_factory=dict)
    pressure_limits: Dict[str, LimitRange] = field(default_factory=dict)
    flow_limits: Dict[str, LimitRange] = field(default_factory=dict)
    vibration_limits: Dict[str, LimitRange] = field(default_factory=dict)
    level_limits: Dict[str, LimitRange] = field(default_factory=dict)
    efficiency_limits: Dict[str, LimitRange] = field(default_factory=dict)
    
    # Metadata
    engineering_units: Dict[str, str] = field(default_factory=dict)
    accuracy: Dict[str, float] = field(default_factory=dict)
    sensor_deadband: float = 1.0  # Percentage
    alarm_delay_sec: float = 5.0
    historian_sampling_sec: float = 10.0
    ai_importance: float = 1.0    # Weight for AI model

    def check_variable(self, variable_name: str, value: float) -> str:
        """Returns the severity string: 'NORMAL', 'ADVISORY', 'WARNING', 'CRITICAL', 'EMERGENCY'"""
        limits_map = getattr(self, f"{variable_name}_limits", None)
        if not limits_map:
            return "NORMAL"
            
        if "EMERGENCY" in limits_map and not limits_map["EMERGENCY"].contains(value):
            return "EMERGENCY"
        if "CRITICAL" in limits_map and not limits_map["CRITICAL"].contains(value):
            return "CRITICAL"
        if "WARNING" in limits_map and not limits_map["WARNING"].contains(value):
            return "WARNING"
        if "ADVISORY" in limits_map and not limits_map["ADVISORY"].contains(value):
            return "ADVISORY"
            
        return "NORMAL"

class ProfileRegistry:
    """Registry holding all centralized Engineering Profiles."""
    _profiles: Dict[str, EngineeringProfile] = {}

    @classmethod
    def register(cls, profile: EngineeringProfile):
        cls._profiles[profile.equipment_type] = profile

    @classmethod
    def get(cls, equipment_type: str) -> Optional[EngineeringProfile]:
        return cls._profiles.get(equipment_type)

# ─── PREDEFINED PROFILES (Calibrated from Phase 10.2) ─────────────────────────

# 1. Production Wells
pw_profile = EngineeringProfile("Production Well")
pw_profile.temperature_limits = {
    "EMERGENCY": LimitRange(85.0, 120.0),
    "CRITICAL": LimitRange(90.0, 115.0),
    "WARNING": LimitRange(92.0, 112.0),
    "ADVISORY": LimitRange(95.0, 110.0),
}
pw_profile.pressure_limits = {
    "EMERGENCY": LimitRange(7.0, 16.0),
    "CRITICAL": LimitRange(7.5, 15.0),
    "WARNING": LimitRange(8.0, 14.0),
    "ADVISORY": LimitRange(8.5, 12.0),
}
pw_profile.flow_limits = {
    "EMERGENCY": LimitRange(30.0, 210.0),
    "CRITICAL": LimitRange(40.0, 200.0),
    "WARNING": LimitRange(45.0, 190.0),
    "ADVISORY": LimitRange(50.0, 180.0),
}
pw_profile.engineering_units = {"temperature": "C", "pressure": "bar", "flow": "m3/h"}
pw_profile.accuracy = {"temperature": 0.1, "pressure": 0.05, "flow": 0.5}
pw_profile.ai_importance = 1.0
ProfileRegistry.register(pw_profile)

# 2. Production Pumps
pp_profile = EngineeringProfile("Production Pump")
pp_profile.vibration_limits = {
    "EMERGENCY": LimitRange(0.0, 7.0),
    "CRITICAL": LimitRange(0.0, 5.0),
    "WARNING": LimitRange(0.0, 3.5),
    "ADVISORY": LimitRange(0.0, 2.5),
}
pp_profile.temperature_limits = {
    "EMERGENCY": LimitRange(0.0, 95.0),
    "CRITICAL": LimitRange(0.0, 85.0),
    "WARNING": LimitRange(0.0, 75.0),
    "ADVISORY": LimitRange(0.0, 65.0),
}
pp_profile.engineering_units = {"vibration": "mm/s", "temperature": "C", "current": "A", "power": "kW"}
pp_profile.ai_importance = 1.5
ProfileRegistry.register(pp_profile)

# 3. Separator
sep_profile = EngineeringProfile("Separator")
sep_profile.level_limits = {
    "EMERGENCY": LimitRange(10.0, 90.0),
    "CRITICAL": LimitRange(20.0, 80.0),
    "WARNING": LimitRange(30.0, 70.0),
    "ADVISORY": LimitRange(40.0, 60.0),
}
sep_profile.pressure_limits = {
    "EMERGENCY": LimitRange(1.0, 5.0),
    "CRITICAL": LimitRange(1.0, 4.0),
    "WARNING": LimitRange(1.2, 3.0),
    "ADVISORY": LimitRange(1.5, 2.5),
}
sep_profile.engineering_units = {"level": "%", "pressure": "bar", "temperature": "C"}
sep_profile.ai_importance = 0.8
ProfileRegistry.register(sep_profile)

# 4. Heat Exchanger
hx_profile = EngineeringProfile("Heat Exchanger")
hx_profile.efficiency_limits = {
    "EMERGENCY": LimitRange(65.0, 100.0),
    "CRITICAL": LimitRange(75.0, 100.0),
    "WARNING": LimitRange(80.0, 100.0),
    "ADVISORY": LimitRange(85.0, 100.0),
}
hx_profile.engineering_units = {"efficiency": "%", "pressure_drop": "bar", "fouling": "index"}
hx_profile.ai_importance = 1.2
ProfileRegistry.register(hx_profile)

# 5. Injection Pumps
inj_profile = EngineeringProfile("Injection Pump")
inj_profile.pressure_limits = {
    "EMERGENCY": LimitRange(7.0, 15.0),
    "CRITICAL": LimitRange(7.5, 13.0),
    "WARNING": LimitRange(8.0, 12.0),
    "ADVISORY": LimitRange(8.5, 11.0),
}
inj_profile.engineering_units = {"pressure": "bar", "flow": "m3/h"}
inj_profile.ai_importance = 0.9
ProfileRegistry.register(inj_profile)

# For backward compatibility, map the old Threshold class variables
class LegacyThresholds:
    TEMP_LO_LO = pw_profile.temperature_limits["CRITICAL"].min_val
    TEMP_LO    = pw_profile.temperature_limits["WARNING"].min_val
    TEMP_HI    = pw_profile.temperature_limits["WARNING"].max_val
    TEMP_HI_HI = pw_profile.temperature_limits["CRITICAL"].max_val

    PRES_LO_LO = pw_profile.pressure_limits["CRITICAL"].min_val
    PRES_LO    = pw_profile.pressure_limits["WARNING"].min_val
    PRES_HI    = pw_profile.pressure_limits["WARNING"].max_val
    PRES_HI_HI = pw_profile.pressure_limits["CRITICAL"].max_val

    FLOW_LO_LO = pw_profile.flow_limits["CRITICAL"].min_val
    FLOW_LO    = pw_profile.flow_limits["WARNING"].min_val
