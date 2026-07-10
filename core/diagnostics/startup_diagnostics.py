"""
core/diagnostics/startup_diagnostics.py
=======================================
Framework for performing a pre-flight health check on all system modules.
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any

logger = logging.getLogger(__name__)

@dataclass
class SystemStatus:
    configuration: str = "UNKNOWN"
    logging: str = "UNKNOWN"
    simulation: str = "UNKNOWN"
    sensors: str = "UNKNOWN"
    historian: str = "UNKNOWN"
    alarms: str = "UNKNOWN"
    dashboard: str = "UNKNOWN"
    digital_twin: str = "UNKNOWN"
    ai_engine: str = "UNKNOWN"
    shap: str = "UNKNOWN"
    optimization: str = "UNKNOWN"
    decision_support: str = "UNKNOWN"
    scenario_sim: str = "UNKNOWN"

class StartupDiagnostics:
    """
    Validates the presence and initializability of key components.
    """
    def __init__(self):
        self.status = SystemStatus()
        self.has_critical_error = False

    def verify_configuration(self):
        try:
            from core.configuration import config
            if config is not None:
                self.status.configuration = "READY"
            else:
                self.status.configuration = "ERROR"
                self.has_critical_error = True
        except Exception as e:
            logger.error(f"Config check failed: {e}")
            self.status.configuration = "ERROR"
            self.has_critical_error = True

    def verify_logging(self):
        try:
            from core.logging.logger_setup import setup_logging
            self.status.logging = "READY"
        except Exception as e:
            self.status.logging = "ERROR"

    def verify_simulation(self):
        try:
            from simulation.plant_simulator import PlantSimulator
            self.status.simulation = "READY"
        except Exception as e:
            logger.warning(f"Simulation check failed: {e}")
            self.status.simulation = "WARNING"

    def verify_sensors(self):
        try:
            from simulation.sensors import GeothermalSensorArray
            self.status.sensors = "READY"
        except Exception as e:
            logger.warning(f"Sensors check failed: {e}")
            self.status.sensors = "WARNING"

    def verify_historian(self):
        try:
            from core.historian.historian import DataHistorian
            self.status.historian = "READY"
        except Exception as e:
            logger.warning(f"Historian check failed: {e}")
            self.status.historian = "WARNING"

    def verify_alarms(self):
        try:
            from scada.alarm_manager import AlarmManager
            self.status.alarms = "READY"
        except Exception as e:
            logger.warning(f"Alarms check failed: {e}")
            self.status.alarms = "WARNING"

    def verify_dashboard(self):
        try:
            from scada.dashboard import SCADADashboard
            self.status.dashboard = "READY"
        except Exception as e:
            logger.warning(f"Dashboard check failed: {e}")
            self.status.dashboard = "WARNING"

    def verify_digital_twin(self):
        try:
            from digital_twin.plant_model.facility import DikiliFacility
            self.status.digital_twin = "READY"
        except Exception as e:
            logger.warning(f"Digital Twin check failed: {e}")
            self.status.digital_twin = "WARNING"

    def verify_ai_engine(self):
        try:
            from analytics.ai.random_forest.predictor import predict_plant_state
            self.status.ai_engine = "READY"
        except Exception as e:
            logger.warning(f"AI Engine check failed: {e}")
            self.status.ai_engine = "WARNING"

    def verify_shap(self):
        try:
            from analytics.ai.shap_explainer import SHAPExplainer
            self.status.shap = "READY"
        except Exception as e:
            logger.warning(f"SHAP check failed: {e}")
            self.status.shap = "WARNING"

    def verify_optimization(self):
        try:
            from analytics.optimization.efficiency_analyzer import EfficiencyAnalyzer
            self.status.optimization = "READY"
        except Exception as e:
            logger.warning(f"Optimization check failed: {e}")
            self.status.optimization = "WARNING"

    def verify_decision_support(self):
        try:
            from analytics.decision_support.decision_engine import DecisionEngine
            self.status.decision_support = "READY"
        except Exception as e:
            logger.warning(f"Decision Support check failed: {e}")
            self.status.decision_support = "WARNING"

    def verify_scenario_sim(self):
        try:
            from analytics.simulation.scenario_runner import ScenarioRunner
            self.status.scenario_sim = "READY"
        except Exception as e:
            logger.warning(f"Scenario Sim check failed: {e}")
            self.status.scenario_sim = "WARNING"

    def run_checks(self):
        """Runs all verification checks."""
        self.verify_configuration()
        self.verify_logging()
        self.verify_simulation()
        self.verify_sensors()
        self.verify_historian()
        self.verify_alarms()
        self.verify_dashboard()
        self.verify_digital_twin()
        self.verify_ai_engine()
        self.verify_shap()
        self.verify_optimization()
        self.verify_decision_support()
        self.verify_scenario_sim()
        self.display_summary()

    def display_summary(self):
        """Prints a clean, formatted startup summary."""
        logger.info("")
        logger.info("============================")
        logger.info("   SYSTEM STARTUP SUMMARY   ")
        logger.info("============================")
        logger.info(f"Configuration ........ {self.status.configuration}")
        logger.info(f"Logging .............. {self.status.logging}")
        logger.info(f"Simulation ........... {self.status.simulation}")
        logger.info(f"Sensor Manager ....... {self.status.sensors}")
        logger.info(f"Historian ............ {self.status.historian}")
        logger.info(f"Alarm Manager ........ {self.status.alarms}")
        logger.info(f"Dashboard ............ {self.status.dashboard}")
        logger.info(f"Digital Twin ......... {self.status.digital_twin}")
        logger.info(f"AI Engine ............ {self.status.ai_engine}")
        logger.info(f"SHAP ................. {self.status.shap}")
        logger.info(f"Optimization ......... {self.status.optimization}")
        logger.info(f"Decision Support ..... {self.status.decision_support}")
        logger.info(f"Scenario Simulation .. {self.status.scenario_sim}")
        logger.info("============================")
        logger.info("Overall Status:")
        
        if self.has_critical_error:
            logger.info("SYSTEM HALTED - CRITICAL ERROR")
            logger.info("============================\n")
            raise RuntimeError("Critical subsystems failed to initialize. Check logs.")
        else:
            logger.info("SYSTEM READY")
            logger.info("============================\n")
