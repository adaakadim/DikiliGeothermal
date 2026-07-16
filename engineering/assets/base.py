"""
engineering/assets/base.py
Base models for all engineering assets in the Digital Twin.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class EngineeringAsset:
    """
    Base model for every equipment and physical asset in the facility.
    """
    asset_id: str
    asset_name: str
    asset_type: str
    status: str = "UNKNOWN"
    installation_date: str = "Unknown"
    design_lifetime_years: float = 0.0
    operating_hours: float = 0.0
    health_index: float = 100.0
    availability: float = 100.0
    maintenance_information: Dict[str, Any] = field(default_factory=dict)
