"""
core/diagnostics/diagnostics_service.py
=======================================
Backend service for tracking system health, CPU, memory, and subsystem statuses.
"""

import time
try:
    import psutil
except ImportError:
    class MockPsutil:
        def cpu_percent(self, interval=None): return 5.0
        def virtual_memory(self):
            class Mem:
                percent = 40.0
            return Mem()
    psutil = MockPsutil()
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class DiagnosticsService:
    """
    Monitors OS-level and application-level metrics.
    """

    def __init__(self):
        self._start_time = time.time()
        self._ai_status = "ONLINE"
        self._comm_status = "ONLINE"
        self._db_status = "ONLINE"
        self._sim_status = "RUNNING"
        self._pred_rate = 0.5  # predictions per sec

    def get_system_metrics(self) -> Dict[str, Any]:
        """
        Return a snapshot of current system diagnostics.
        """
        uptime_seconds = int(time.time() - self._start_time)
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours:02d}h {minutes:02d}m {seconds:02d}s"

        metrics = {
            "CPU Usage (%)": psutil.cpu_percent(interval=None),
            "Memory Usage (%)": psutil.virtual_memory().percent,
            "Uptime": uptime_str,
            "AI Engine": self._ai_status,
            "Communications": self._comm_status,
            "Historian DB": self._db_status,
            "Simulation": self._sim_status,
            "Prediction Rate (Hz)": self._pred_rate
        }
        return metrics

    def update_status(self, subsystem: str, status: str):
        """Update the health status of a specific subsystem."""
        if subsystem == "AI":
            self._ai_status = status
        elif subsystem == "COMMS":
            self._comm_status = status
        elif subsystem == "DB":
            self._db_status = status
        elif subsystem == "SIM":
            self._sim_status = status
