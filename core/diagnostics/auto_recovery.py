"""
core/diagnostics/auto_recovery.py
=================================
Self-Diagnostics & Auto Recovery Engine for DikiliGeothermal SCADA.
Periodically performs health checks on modules and attempts automated recovery.
"""

import time
import logging
from dataclasses import dataclass
from typing import Dict, List, Callable, Any, Optional

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

from core.config.system_config import SystemConfig, RecoveryPolicy
from core.diagnostics.communication_monitor import CommunicationMonitor, ModuleStatus

logger = logging.getLogger(__name__)

@dataclass
class RecoveryRecord:
    timestamp: float
    module_name: str
    failure_type: str
    action_taken: str
    duration_sec: float
    success: bool


class SelfDiagnosticsEngine:
    """
    Centralised engine for self-monitoring and auto-recovery of SCADA modules.
    Reuses the CommunicationMonitor for baseline health checks.
    """
    
    def __init__(self, comm_monitor: CommunicationMonitor, config: SystemConfig):
        self.monitor = comm_monitor
        self.config = config
        self.policies: Dict[str, RecoveryPolicy] = config.recovery_policies
        self.recovery_handlers: Dict[str, Callable[[], bool]] = {}
        
        # State tracking
        self.recovery_history: List[RecoveryRecord] = []
        self._retry_counts: Dict[str, int] = {}
        self._last_retry_time: Dict[str, float] = {}
        self._failed_modules: set = set()
        
        # Notification callback (set by scada/system.py)
        self.on_notification: Optional[Callable[[str, str], None]] = None
        
        logger.info("Self-Diagnostics & Auto Recovery Engine initialised.")

    def register_recovery_handler(self, module_name: str, handler: Callable[[], bool]):
        """Register a callback function to attempt recovery of a specific module."""
        self.recovery_handlers[module_name] = handler
        logger.debug(f"Registered recovery handler for {module_name}")

    def evaluate(self):
        """
        Evaluate system health and trigger recoveries if needed.
        Called periodically (e.g., every SCADA tick).
        """
        now = time.time()
        
        # Monitor exposes the current status of all registered modules
        for module_name, mod_info in self.monitor.modules.items():
            status = mod_info.status
            
            # Module is healthy or recovering
            if status in (ModuleStatus.ONLINE, ModuleStatus.STARTING, ModuleStatus.WARNING):
                if module_name in self._failed_modules:
                    self._failed_modules.remove(module_name)
                    self._retry_counts[module_name] = 0
                continue
                
            # Module is offline or failed
            if status in (ModuleStatus.FAILED, ModuleStatus.OFFLINE):
                self._handle_failure(module_name, now)

    def _handle_failure(self, module_name: str, current_time: float):
        """Process a detected failure according to its recovery policy."""
        policy = self.policies.get(module_name, RecoveryPolicy.default())
        
        if policy.manual_recovery_required:
            if module_name not in self._failed_modules:
                self._notify(module_name, "CRIT", f"{module_name} failed. Manual intervention required.")
                self._failed_modules.add(module_name)
            return

        retries = self._retry_counts.get(module_name, 0)
        if retries >= policy.max_retries:
            if module_name not in self._failed_modules:
                self._notify(module_name, "CRIT", f"{module_name} failed. Max retries ({policy.max_retries}) exceeded.")
                self._failed_modules.add(module_name)
            return
            
        last_retry = self._last_retry_time.get(module_name, 0)
        if current_time - last_retry < policy.retry_delay_sec:
            return  # Waiting for retry delay
            
        # Attempt recovery
        self._attempt_recovery(module_name, current_time)

    def _attempt_recovery(self, module_name: str, current_time: float):
        """Execute the registered recovery handler for the module."""
        self._retry_counts[module_name] = self._retry_counts.get(module_name, 0) + 1
        self._last_retry_time[module_name] = current_time
        
        handler = self.recovery_handlers.get(module_name)
        if not handler:
            logger.warning(f"No recovery handler registered for {module_name}")
            return
            
        self._notify(module_name, "WARN", f"Attempting automatic recovery for {module_name} (Attempt {self._retry_counts[module_name]})...")
        
        start_t = time.time()
        try:
            success = handler()
        except Exception as e:
            logger.error(f"Error during recovery of {module_name}: {e}")
            success = False
        duration = time.time() - start_t
        
        # Log History
        record = RecoveryRecord(
            timestamp=current_time,
            module_name=module_name,
            failure_type="Comm/Status Failure",
            action_taken="Invoked recovery handler",
            duration_sec=duration,
            success=success
        )
        self.recovery_history.append(record)
        
        if success:
            self._notify(module_name, "INFO", f"{module_name} recovered successfully.")
            self._retry_counts[module_name] = 0
            if module_name in self._failed_modules:
                self._failed_modules.remove(module_name)
            # Reset monitor status to prevent immediate re-trigger
            mod = self.monitor.modules.get(module_name)
            if mod:
                mod.status = ModuleStatus.ONLINE
                mod.error_count = 0
        else:
            self._notify(module_name, "WARN", f"Recovery attempt {self._retry_counts[module_name]} failed for {module_name}.")
            
    def _notify(self, module_name: str, level: str, message: str):
        """Log event and escalate to operator."""
        log_method = logger.info if level == "INFO" else (logger.warning if level == "WARN" else logger.error)
        log_method(f"[{module_name}] {message}")
        
        if self.on_notification:
            self.on_notification(level, message)

    def get_diagnostic_report(self) -> Dict[str, Any]:
        """Generate a diagnostic summary of the SCADA system."""
        healthy = []
        recovering = []
        failed = list(self._failed_modules)
        
        for name, mod in self.monitor.modules.items():
            if mod.status == ModuleStatus.ONLINE:
                healthy.append(name)
            elif mod.status in (ModuleStatus.STARTING, ModuleStatus.WARNING):
                recovering.append(name)
                
        successful_recoveries = len([r for r in self.recovery_history if r.success])
        failed_recoveries = len([r for r in self.recovery_history if not r.success])
        
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory().percent
        
        overall_health = "GOOD"
        if failed:
            overall_health = "CRITICAL"
        elif recovering:
            overall_health = "WARNING"
            
        return {
            "Overall Health": overall_health,
            "Healthy Modules": healthy,
            "Recovered Modules": successful_recoveries,
            "Failed Recoveries": failed_recoveries,
            "Pending Issues": failed + recovering,
            "CPU Usage (%)": cpu,
            "Memory Usage (%)": mem,
            "Total Monitored": len(self.monitor.modules)
        }
