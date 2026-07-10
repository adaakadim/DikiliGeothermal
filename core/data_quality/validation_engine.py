"""
core/data_quality/validation_engine.py
======================================
Professional Data Validation and Sensor Health Engine.
Monitors incoming sensor streams for staleness, range violations,
and evaluates AI input vectors before prediction.
"""

import time
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Tuple, Optional

logger = logging.getLogger(__name__)

class HealthState(Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    WARNING = "WARNING"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"

@dataclass
class SensorDiagnostics:
    tag: str
    last_update_time: float = 0.0
    last_value: Optional[float] = None
    repeated_count: int = 0
    health: HealthState = HealthState.UNKNOWN
    quality_score: float = 100.0
    error_count: int = 0
    warning_count: int = 0

class ValidationEngine:
    def __init__(self):
        # Configuration
        self.stale_timeout_sec = 30.0  # Seconds before considered offline
        self.max_repeated_values = 15  # Ticks before warning for stuck sensor
        
        # Engineering Limits
        self.limits = {
            "temperature_c": {"min": 50.0, "max": 120.0},
            "pressure_bar": {"min": 1.0, "max": 20.0},
            "flow_m3h": {"min": 0.0, "max": 400.0}
        }
        
        # State tracking
        self._sensors: Dict[str, SensorDiagnostics] = {}
        self._last_watchdog_time = time.time()
        
        self.global_quality_score = 100.0

    def _get_diag(self, tag: str) -> SensorDiagnostics:
        if tag not in self._sensors:
            self._sensors[tag] = SensorDiagnostics(tag=tag)
        return self._sensors[tag]

    def validate_sensors(self, readings: list, current_time: float) -> Tuple[List[str], List[str]]:
        """
        Validates raw SensorReading objects.
        Returns: (warnings, errors)
        """
        warnings = []
        errors = []
        
        # 1. Communication Watchdog
        delta_t = current_time - self._last_watchdog_time
        if delta_t > 5.0:
            warnings.append(f"[WATCHDOG] High loop latency detected: {delta_t:.1f}s")
        self._last_watchdog_time = current_time
        
        # 2. Process Readings
        for r in readings:
            tag = r.well_id
            diag = self._get_diag(tag)
            
            # Stale Data Check
            if r.timestamp <= diag.last_update_time:
                diag.warning_count += 1
                warnings.append(f"[STALE] {tag} timestamp not advancing.")
            
            # Stuck Value Check (using temperature as proxy for staleness)
            if diag.last_value is not None and abs(r.temperature_c - diag.last_value) < 0.001:
                diag.repeated_count += 1
                if diag.repeated_count > self.max_repeated_values:
                    diag.warning_count += 1
                    warnings.append(f"[STUCK] {tag} values frozen for {diag.repeated_count} ticks.")
            else:
                diag.repeated_count = 0
                
            diag.last_update_time = r.timestamp
            diag.last_value = r.temperature_c
            
            # Range Checks
            if not self._check_range("temperature_c", r.temperature_c):
                diag.error_count += 1
                errors.append(f"[RANGE] {tag} temperature {r.temperature_c} out of bounds.")
            if not self._check_range("pressure_bar", r.pressure_bar):
                diag.error_count += 1
                errors.append(f"[RANGE] {tag} pressure {r.pressure_bar} out of bounds.")
            if not self._check_range("flow_m3h", r.flow_m3h):
                diag.error_count += 1
                errors.append(f"[RANGE] {tag} flow {r.flow_m3h} out of bounds.")
                
            # Compute Health
            if diag.error_count > 0:
                diag.health = HealthState.FAILED
                diag.quality_score = max(0.0, 100.0 - (diag.error_count * 15.0))
            elif diag.warning_count > 0 or not r.is_healthy:
                diag.health = HealthState.WARNING
                diag.quality_score = max(50.0, 100.0 - (diag.warning_count * 5.0))
            else:
                diag.health = HealthState.ONLINE
                diag.quality_score = min(100.0, diag.quality_score + 1.0) # Slowly recover
                
            # Decay counters slowly
            if diag.error_count > 0 and random_decay(): diag.error_count -= 1
            if diag.warning_count > 0 and random_decay(): diag.warning_count -= 1
            
        # 3. Detect Offline Sensors
        for tag, diag in self._sensors.items():
            if current_time - diag.last_update_time > self.stale_timeout_sec:
                if diag.health != HealthState.OFFLINE:
                    diag.health = HealthState.OFFLINE
                    diag.quality_score = 0.0
                    errors.append(f"[OFFLINE] Sensor {tag} stopped communicating.")
                    
        # Update Global Score
        if self._sensors:
            self.global_quality_score = sum(d.quality_score for d in self._sensors.values()) / len(self._sensors)
            
        return warnings, errors

    def validate_ai_inputs(self, live_data: Dict[str, float]) -> Tuple[List[str], List[str]]:
        """
        Validates the compiled feature vector before sending to the AI engine.
        Returns: (warnings, errors)
        """
        warnings = []
        errors = []
        
        required_keys = ["Temperature (°C)", "Pressure (bar)", "Flow Rate (m3/h)"]
        for key in required_keys:
            if key not in live_data:
                errors.append(f"[AI_VALIDATION] Missing critical feature: {key}")
                
        for k, v in live_data.items():
            if v is None:
                errors.append(f"[AI_VALIDATION] Null value for feature: {k}")
            elif isinstance(v, float):
                # Basic NaN / Inf check
                if v != v or v == float('inf') or v == float('-inf'):
                    errors.append(f"[AI_VALIDATION] Invalid numeric (NaN/Inf) for feature: {k}")
                # Negative check for physicals
                if "Pressure" in k and v < 0:
                    errors.append(f"[AI_VALIDATION] Negative pressure detected: {v:.2f} in {k}")
                if "Flow" in k and v < -10: # allow slight reverse noise
                    errors.append(f"[AI_VALIDATION] High negative flow detected: {v:.2f} in {k}")
                    
        return warnings, errors

    def _check_range(self, metric: str, value: float) -> bool:
        if metric in self.limits:
            return self.limits[metric]["min"] <= value <= self.limits[metric]["max"]
        return True

def random_decay():
    import random
    return random.random() < 0.1
