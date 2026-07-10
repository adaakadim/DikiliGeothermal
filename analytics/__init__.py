"""
analytics/__init__.py
Analytics Package — KPIs, trend analysis, reporting, fault detection
"""
from .kpi_engine import KPIEngine
from .trend_analyzer import TrendAnalyzer
from .reporter import ReportGenerator
from .fault_detector import (
    FaultDetector,
    FaultReport,
    SystemHealth,
    DetectorConfig,
    FaultFactor,
)
from .matplotlib_dashboard import SCADAPlotDashboard

__all__ = [
    "KPIEngine",
    "TrendAnalyzer",
    "ReportGenerator",
    "FaultDetector",
    "FaultReport",
    "SystemHealth",
    "DetectorConfig",
    "FaultFactor",
    "SCADAPlotDashboard",
]


