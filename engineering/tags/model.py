"""
engineering/tags/model.py
Detailed model for all engineering tags in the digital twin subsystem.
"""

from dataclasses import dataclass, field
from typing import Optional

@dataclass
class EngineeringTag:
    """
    Standardized engineering tag representing a single process variable.
    """
    tag_id: str
    display_name: str
    description: str
    engineering_unit: str
    
    # Ranges
    normal_range: tuple[float, float] = (0.0, 100.0)
    warning_range: tuple[float, float] = (0.0, 100.0)
    critical_range: tuple[float, float] = (0.0, 100.0)
    
    # Sampling and Persistence
    scan_rate: float = 1.0 # seconds
    historian_enabled: bool = True
    trend_enabled: bool = True
    
    # Subsystems
    alarm_enabled: bool = True
    ai_enabled: bool = True
    dashboard_visible: bool = True
    digital_twin_visible: bool = True
    
    # Physics / Instrumentation specifics
    accuracy: str = "+/- 1%"
    deadband: float = 0.0
    last_calibration: str = "Unknown"
