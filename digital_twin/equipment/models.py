"""
digital_twin/equipment/models.py
================================
Digital Twin abstract base models and concrete classes representing
physical equipment in the Dikili Geothermal Plant.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List

@dataclass
class Equipment:
    """Base class for all digital twin equipment components."""
    id: str
    name: str
    type: str
    status: str = "OFFLINE"
    health_score: float = 100.0
    failure_risk: float = 0.0
    ai_confidence: float = 0.0
    ai_recommendation: str = "No data"
    sensors: Dict[str, float] = field(default_factory=dict)
    alarms: List[str] = field(default_factory=list)
    positive_factors: List[str] = field(default_factory=list)
    negative_factors: List[str] = field(default_factory=list)
    explanation_text: str = ""
    
    # Maintenance Schedule
    last_maintenance_date: str = "Unknown"
    next_planned_maintenance: str = "Unknown"
    
    # RUL properties
    rul_hours: float = 0.0
    estimated_days: float = 0.0
    rul_confidence: float = 0.0
    degradation_rate: float = 0.0
    degradation_trend: str = "Unknown"
    maintenance_priority: str = "Unknown"
    
    # Optimization properties
    efficiency: float = 0.0
    target_efficiency: float = 0.0
    optimization_suggestion: str = ""
    estimated_improvement: str = ""
    
    # Anomaly detection properties
    anomaly_score: float = 0.0
    anomaly_status: str = "Normal"
    anomaly_root_cause: str = ""
    anomaly_recommendation: str = ""
    
    # Phase 5.5.6 Decision Support properties
    decision_support: Dict[str, Any] = field(default_factory=dict)
    
    operating_hours: float = 0.0
    motor_current: float = 0.0
    power_consumption: float = 0.0
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        from digital_twin.asset_registry import AssetRegistry
        self.metadata = AssetRegistry().get_asset(self.id)

    
    def update_sensor(self, key: str, value: float):
        self.sensors[key] = value
        if key == "Motor Current (A)": self.motor_current = value
        if key == "Power (kW)": self.power_consumption = value
        if key == "Operating Hours": self.operating_hours = value

    def update_ai(self, health: float, risk: float, conf: float, rec: str, pos: List[str]=None, neg: List[str]=None, expl: str=""):
        self.health_score = health
        self.failure_risk = risk
        self.ai_confidence = conf
        self.ai_recommendation = rec
        self.explanation_text = expl
        if pos is not None: self.positive_factors = pos
        if neg is not None: self.negative_factors = neg

    def update_rul(self, hours: float, days: float, conf: float, deg_rate: float, trend: str, priority: str):
        self.rul_hours = hours
        self.estimated_days = days
        self.rul_confidence = conf
        self.degradation_rate = deg_rate
        self.degradation_trend = trend
        self.maintenance_priority = priority

    def update_optimization(self, eff: float, target: float, sugg: str, est_imp: str):
        self.efficiency = eff
        self.target_efficiency = target
        self.optimization_suggestion = sugg
        self.estimated_improvement = est_imp

    def update_anomaly(self, score: float, status: str, root_cause: str, recommendation: str):
        self.anomaly_score = score
        self.anomaly_status = status
        self.anomaly_root_cause = root_cause
        self.anomaly_recommendation = recommendation

    def update_decision_support(self, data: Dict[str, Any]):
        self.decision_support = data

    def evaluate_status(self):
        """Determine base operational status from risk/alarms."""
        if self.alarms:
            self.status = "CRITICAL"
            return
        if self.failure_risk > 60:
            self.status = "CRITICAL"
        elif self.failure_risk > 35:
            self.status = "WARNING"
        elif self.health_score < 70:
            self.status = "MAINTENANCE REQUIRED"
        else:
            self.status = "NORMAL"

@dataclass
class GeothermalWell(Equipment):
    def evaluate_status(self):
        if self.sensors.get("Flow Rate", 0) < 10:
            self.status = "OFFLINE"
            return
        super().evaluate_status()

@dataclass
class ReinjectionWell(Equipment):
    def evaluate_status(self):
        if self.sensors.get("Flow Rate", 0) < 10:
            self.status = "OFFLINE"
            return
        super().evaluate_status()

@dataclass
class Pump(Equipment):
    def evaluate_status(self):
        if self.sensors.get("Flow Rate", 0) < 10:
            self.status = "OFFLINE"
            return
        super().evaluate_status()

@dataclass
class HeatExchanger(Equipment):
    def evaluate_status(self):
        if self.sensors.get("Thermal Power", 0) < 0.1:
            self.status = "STANDBY"
            return
        super().evaluate_status()

@dataclass
class Separator(Equipment):
    def evaluate_status(self):
        if self.sensors.get("Pressure", 0) < 1.0:
            self.status = "OFFLINE"
            return
        super().evaluate_status()

@dataclass
class Pipeline(Equipment):
    pass

@dataclass
class Valve(Equipment):
    def evaluate_status(self):
        # A valve might have Position sensor (0-100%)
        pos = self.sensors.get("Position", 100)
        if pos >= 95:
            self.status = "FULLY OPEN"
        elif pos <= 5:
            self.status = "CLOSED"
        else:
            self.status = "PARTIALLY OPEN"
        
        # Override if alarms or high risk exist
        if self.alarms:
            self.status = "CRITICAL"
        elif self.failure_risk > 60:
            self.status = "CRITICAL"
        elif self.failure_risk > 35:
            self.status = "WARNING"
