"""
core/safety/fail_safe.py
========================
Automatic Fail-Safe & Safe Operation Manager.
Monitors critical system conditions and enforces predefined safe actions.
"""

import time
import logging
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable

from core.config.system_config import SystemConfig

logger = logging.getLogger(__name__)

class SafeMode(Enum):
    NORMAL = 0
    WARNING = 1
    SAFE_MODE = 2
    CRITICAL = 3
    EMERGENCY = 4

@dataclass
class FailSafeEvent:
    timestamp: float
    mode: SafeMode
    description: str
    is_recovery: bool = False

class FailSafeManager:
    """
    Centralized manager for Automatic Fail-Safe & Safe Operation.
    """
    def __init__(self, config: SystemConfig):
        self.config = config
        self.current_mode: SafeMode = SafeMode.NORMAL
        
        # Track active failures (by component or tag)
        self.active_failures: Dict[str, str] = {}
        self.recovered_failures: List[str] = []
        
        # Recovery state
        self._pending_recovery: bool = False
        self._recovery_start_time: float = 0.0
        self.last_recovery_time: Optional[float] = None
        
        # Event log
        self.events: List[FailSafeEvent] = []
        
        # Notification callback (for HMI)
        self.on_notification: Optional[Callable[[str, SafeMode], None]] = None
        
        logger.info("Fail-Safe Manager initialized.")

    def log_event(self, description: str, mode: SafeMode, is_recovery: bool = False):
        """Record an event and trigger notifications."""
        event = FailSafeEvent(time.time(), mode, description, is_recovery)
        self.events.append(event)
        
        if is_recovery:
            logger.info(f"[FAIL-SAFE RECOVERY] {description}")
        else:
            logger.warning(f"[FAIL-SAFE {mode.name}] {description}")
            
        if self.on_notification:
            self.on_notification(description, mode)

    def report_failure(self, component_id: str, description: str):
        """Report a failure in a subsystem (e.g., Sensor, AI, DB)."""
        if component_id not in self.active_failures:
            self.active_failures[component_id] = description
            self._evaluate_mode()

    def report_recovery(self, component_id: str):
        """Report that a previously failed subsystem is operating normally again."""
        if component_id in self.active_failures:
            desc = self.active_failures.pop(component_id)
            if desc not in self.recovered_failures:
                self.recovered_failures.append(desc)
            self._evaluate_mode()

    def _evaluate_mode(self):
        """Determine the correct SafeMode based on active failures."""
        num_failures = len(self.active_failures)
        new_mode = SafeMode.NORMAL
        
        if num_failures > 0:
            if num_failures >= getattr(self.config, 'max_sensor_failures', 2):
                new_mode = SafeMode.CRITICAL
            else:
                new_mode = SafeMode.SAFE_MODE
                
        self._transition_mode(new_mode)

    def _transition_mode(self, target_mode: SafeMode):
        """Handle state transitions with recovery validation."""
        now = time.time()
        
        # Escalating severity
        if target_mode.value > self.current_mode.value:
            self._pending_recovery = False
            self.current_mode = target_mode
            self.log_event(f"System operating in {target_mode.name} mode.", target_mode)
            
            if target_mode.value >= SafeMode.SAFE_MODE.value:
                self.log_event("AI temporarily disabled due to active failures.", target_mode)
                
        # Decreasing severity (requires recovery validation)
        elif target_mode.value < self.current_mode.value:
            if getattr(self.config, 'auto_recovery_enabled', True):
                if not self._pending_recovery:
                    # Start the validation timer
                    self._pending_recovery = True
                    self._recovery_start_time = now
                    logger.info(f"Failures cleared. Verifying system integrity for {getattr(self.config, 'recovery_validation_time_sec', 15.0)}s...")
                
                # Check if validation period has elapsed
                if now - self._recovery_start_time >= getattr(self.config, 'recovery_validation_time_sec', 15.0):
                    self.current_mode = target_mode
                    self._pending_recovery = False
                    self.last_recovery_time = now
                    self.log_event(f"System integrity verified. Returned to {target_mode.name}.", target_mode, is_recovery=True)
            else:
                # Manual recovery required (stub)
                pass

    def tick(self):
        """Periodic evaluation (e.g., for recovery validation)."""
        if self._pending_recovery:
            # Re-evaluate mode to trigger validation completion
            self._evaluate_mode()

    def is_ai_allowed(self) -> bool:
        """Returns True if the AI prediction engine is permitted to run."""
        return self.current_mode.value < SafeMode.SAFE_MODE.value


# ─── Redundancy Management Interfaces (For future extension) ───────────

class BackupAIEngine:
    """Interface for a future redundant AI Engine."""
    def take_over(self):
        raise NotImplementedError

class BackupHistorian:
    """Interface for a future redundant Historian database."""
    def take_over(self):
        raise NotImplementedError

class BackupConfiguration:
    """Interface for redundant configuration management."""
    def switch_to_backup(self):
        raise NotImplementedError
