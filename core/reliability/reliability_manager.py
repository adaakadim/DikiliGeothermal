"""
core/reliability/reliability_manager.py
=======================================
Enterprise Industrial Reliability & Resilience Framework.
Continuously monitors subsystems, logs events, and exposes health status.
"""

import time
import logging
import json
from pathlib import Path
from enum import Enum
from typing import Dict, Any

logger = logging.getLogger("core.reliability")

class SubsystemStatus(Enum):
    ONLINE = "ONLINE"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"
    RECOVERING = "RECOVERING"

class ReliabilityManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ReliabilityManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self._subsystems: Dict[str, SubsystemStatus] = {
            "Sensor Quality": SubsystemStatus.ONLINE,
            "Communication": SubsystemStatus.ONLINE,
            "Historian": SubsystemStatus.ONLINE,
            "AI Engine": SubsystemStatus.ONLINE,
            "Digital Twin": SubsystemStatus.ONLINE,
            "Scheduler": SubsystemStatus.ONLINE
        }
        
        self.log_path = Path("logs/reliability.log")
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._initialized = True
        logger.info("Reliability Manager initialized.")

    def update_status(self, subsystem: str, status: SubsystemStatus, event: str = "", severity: str = "INFO", recovery_action: str = "None"):
        """Update a subsystem's status and log the reliability event."""
        if subsystem not in self._subsystems:
            self._subsystems[subsystem] = SubsystemStatus.ONLINE

        old_status = self._subsystems[subsystem]
        
        if old_status != status or severity in ["WARNING", "CRITICAL", "ERROR"]:
            self._subsystems[subsystem] = status
            
            # Log event
            log_entry = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "subsystem": subsystem,
                "status": status.value,
                "event": event,
                "severity": severity,
                "recovery_action": recovery_action
            }
            
            with open(self.log_path, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
                
            logger_func = logger.info
            if severity in ["WARNING", "ERROR"]:
                logger_func = logger.warning
            elif severity == "CRITICAL":
                logger_func = logger.error
                
            logger_func(f"[RELIABILITY] {subsystem} transitioned to {status.value}. Event: {event}. Recovery: {recovery_action}")

    def get_status(self, subsystem: str) -> SubsystemStatus:
        return self._subsystems.get(subsystem, SubsystemStatus.ONLINE)

    def get_all_statuses(self) -> Dict[str, str]:
        return {k: v.value for k, v in self._subsystems.items()}

# Global singleton
reliability_manager = ReliabilityManager()
