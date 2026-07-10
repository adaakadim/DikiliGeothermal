"""
scada/config.py
System configuration — loaded from JSON, with sensible defaults.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

# ─── Well / Source Definition ─────────────────────────────────────────────────
@dataclass
class GeothermalWell:
    well_id: str
    name: str
    depth_m: float               # metres
    reservoir_temp_c: float      # °C at reservoir depth
    max_flow_m3h: float          # m³/h
    nominal_pressure_bar: float  # bar

# ─── Network Zone ─────────────────────────────────────────────────────────────
@dataclass
class DistrictHeatingZone:
    zone_id: str
    name: str
    subscriber_count: int
    design_load_mw: float        # MW

# ─── Workspace Configuration ───────────────────────────────────────────────────
@dataclass
class WorkspaceConfig:
    sidebar_width: int = 280
    last_panel: str = "overview"
    alarm_filter_severity: str = "ALL"
    alarm_filter_status: str = "ALL"

# ─── Feature Configuration ─────────────────────────────────────────────────────
@dataclass
class FeatureConfig:
    ai_engine: bool = True
    digital_twin: bool = True
    historian: bool = True
    scheduler: bool = True
    performance_monitor: bool = True
    reliability_framework: bool = True
    security_features: bool = True
    opcua_driver: bool = False
    modbus_driver: bool = False
    mqtt_driver: bool = False

# ─── Driver Configuration ──────────────────────────────────────────────────────
@dataclass
class DriverConfig:
    active_driver: str = "simulation"
    connection_timeout_sec: float = 5.0
    max_retries: int = 3

# ─── Recovery Policy ──────────────────────────────────────────────────────────
@dataclass
class RecoveryPolicy:
    max_retries: int = 3
    retry_delay_sec: float = 5.0
    manual_recovery_required: bool = False
    
    @classmethod
    def default(cls) -> "RecoveryPolicy":
        return cls()
        
    @classmethod
    def critical(cls) -> "RecoveryPolicy":
        return cls(max_retries=5, retry_delay_sec=2.0)
        
    @classmethod
    def manual(cls) -> "RecoveryPolicy":
        return cls(max_retries=0, manual_recovery_required=True)

# ─── Main Config ──────────────────────────────────────────────────────────────
@dataclass
class SystemConfig:
    plant_name: str = "Dikili Geothermal District Heating Plant"
    location: str = "Dikili, Izmir, Turkey"
    latitude: float = 39.0706
    longitude: float = 26.8905
    scan_interval: float = 2.0          # seconds per SCADA tick
    alarm_check_interval: float = 1.0   # seconds
    historian_flush_interval: float = 10.0  # seconds
    simulation_mode: bool = True
    log_level: str = "INFO"
    theme: str = "dark"                 # "dark" or "light"
    workspace: WorkspaceConfig = field(default_factory=WorkspaceConfig)
    features: FeatureConfig = field(default_factory=FeatureConfig)
    drivers: DriverConfig = field(default_factory=DriverConfig)
    
    # Comms settings
    opcua_endpoint: str = "opc.tcp://localhost:4840"
    modbus_host: str = "127.0.0.1"
    modbus_port: int = 502
    mqtt_broker: str = "mqtt://localhost:1883"
    
    # Database settings
    db_path: str = "data/historian.db"
    
    # AI Thresholds
    ai_risk_warning_threshold: float = 40.0
    ai_risk_critical_threshold: float = 70.0

    # Process limits
    max_wellhead_temp_c: float = 115.0
    min_wellhead_temp_c: float = 60.0
    max_system_pressure_bar: float = 16.0
    min_system_pressure_bar: float = 2.5
    max_flow_m3h: float = 350.0
    min_flow_m3h: float = 20.0

    # Heat exchanger
    hx_efficiency: float = 0.92         # 92 %
    target_supply_temp_c: float = 85.0
    target_return_temp_c: float = 55.0

    # Fail-Safe Manager Settings
    max_sensor_failures: int = 2
    recovery_validation_time_sec: float = 15.0
    auto_recovery_enabled: bool = True
    
    # Recovery Policies mapping (Module Name -> Policy)
    recovery_policies: dict = field(default_factory=lambda: {
        "Historian": RecoveryPolicy.default(),
        "AI Engine": RecoveryPolicy.critical(),
        "SCADA Core": RecoveryPolicy.manual(),
        "Tag Database": RecoveryPolicy.critical(),
        "Alarm Manager": RecoveryPolicy.default(),
        "Digital Twin": RecoveryPolicy.default(),
        "Simulation Engine": RecoveryPolicy.default(),
        "Sensor Manager": RecoveryPolicy.default(),
        "Configuration Manager": RecoveryPolicy.default(),
        "Decision Support": RecoveryPolicy.default(),
    })

    # Geothermal wells
    wells: List[GeothermalWell] = field(default_factory=lambda: [
        GeothermalWell("W-01", "Dikili-1", 950, 105, 180, 8.5),
        GeothermalWell("W-02", "Dikili-2", 1100, 112, 210, 9.2),
        GeothermalWell("W-03", "Dikili-3", 870,  98, 140, 7.8),
    ])

    # District heating zones
    zones: List[DistrictHeatingZone] = field(default_factory=lambda: [
        DistrictHeatingZone("Z-A", "Zone A — Residential North",  1240, 4.2),
        DistrictHeatingZone("Z-B", "Zone B — Commercial Centre",   320, 2.8),
        DistrictHeatingZone("Z-C", "Zone C — Residential South",   890, 3.1),
        DistrictHeatingZone("Z-D", "Zone D — Industrial West",     150, 5.6),
    ])

    # ── Serialisation helpers ─────────────────────────────────────────────────
    @classmethod
    def load(cls, path: str = None) -> "SystemConfig":
        """
        Loads the system configuration via the new ConfigManager.
        'path' is ignored but kept for backward compatibility.
        """
        from core.configuration import config as cm
        
        cfg = cls()
        cfg.plant_name = cm.get("app.name", cfg.plant_name)
        cfg.location = cm.get("app.location", cfg.location)
        cfg.latitude = cm.get("app.latitude", cfg.latitude)
        cfg.longitude = cm.get("app.longitude", cfg.longitude)
        
        cfg.scan_interval = cm.get("scada.scan_interval_sec", cfg.scan_interval)
        cfg.alarm_check_interval = cm.get("scada.alarm_check_interval_sec", cfg.alarm_check_interval)
        
        # Features mapping
        cfg.features.ai_engine = cm.get("features.ai_engine", cfg.features.ai_engine)
        cfg.features.digital_twin = cm.get("features.digital_twin", cfg.features.digital_twin)
        cfg.features.historian = cm.get("features.historian", cfg.features.historian)
        cfg.features.scheduler = cm.get("features.scheduler", cfg.features.scheduler)
        cfg.features.performance_monitor = cm.get("features.performance_monitor", cfg.features.performance_monitor)
        cfg.features.reliability_framework = cm.get("features.reliability_framework", cfg.features.reliability_framework)
        cfg.features.security_features = cm.get("features.security_features", cfg.features.security_features)
        cfg.features.opcua_driver = cm.get("features.opcua_driver", cfg.features.opcua_driver)
        cfg.features.modbus_driver = cm.get("features.modbus_driver", cfg.features.modbus_driver)
        cfg.features.mqtt_driver = cm.get("features.mqtt_driver", cfg.features.mqtt_driver)

        # Drivers mapping
        cfg.drivers.active_driver = cm.get("drivers.active_driver", cfg.drivers.active_driver)
        cfg.drivers.connection_timeout_sec = cm.get("drivers.connection_timeout_sec", cfg.drivers.connection_timeout_sec)
        cfg.drivers.max_retries = cm.get("drivers.max_retries", cfg.drivers.max_retries)
        
        cfg.historian_flush_interval = cm.get("scada.historian_flush_interval_sec", cfg.historian_flush_interval)
        cfg.simulation_mode = cm.get("scada.simulation_mode", cfg.simulation_mode)
        
        cfg.log_level = cm.get("logging.level", cfg.log_level)
        cfg.theme = cm.get("gui.theme", cfg.theme)
        
        cfg.opcua_endpoint = cm.get("connectivity.opcua_endpoint", cfg.opcua_endpoint)
        cfg.modbus_host = cm.get("connectivity.modbus_host", cfg.modbus_host)
        cfg.modbus_port = cm.get("connectivity.modbus_port", cfg.modbus_port)
        cfg.mqtt_broker = cm.get("connectivity.mqtt_broker", cfg.mqtt_broker)
        
        logger.info(f"SystemConfig loaded from Environment: {cm.environment}")
        return cfg

    def save(self, path: str):
        # Configuration saving is not supported in the new YAML structure
        # to prevent application code from mutating infrastructure configuration.
        logger.warning("SystemConfig.save() called, but YAML configs are immutable at runtime.")
