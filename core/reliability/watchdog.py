"""
core/reliability/watchdog.py
============================
Enterprise Watchdog Framework to monitor process heartbeats and flag timeouts.
"""

import time
import logging
import threading
from typing import Dict, Any, List, Optional

logger = logging.getLogger("core.reliability.watchdog")

class WatchdogState:
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"

class MonitoredService:
    def __init__(self, name: str, expected_interval_s: float, timeout_s: float):
        self.name = name
        self.expected_interval_s = expected_interval_s
        self.timeout_s = timeout_s
        self.last_heartbeat = time.time()
        self.missed_heartbeats = 0
        self.state = WatchdogState.HEALTHY
        self.consecutive_missed = 0

class WatchdogEngine:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(WatchdogEngine, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self._services: Dict[str, MonitoredService] = {}
        
        # Load configs
        from core.configuration import config
        self._default_timeout = config.get("performance.watchdog.default_timeout_s", 5.0)
        self._warn_misses = config.get("performance.watchdog.warning_threshold_misses", 2)
        self._fail_misses = config.get("performance.watchdog.failed_threshold_misses", 4)
        
        self._initialized = True

    def register_service(self, name: str, expected_interval_s: float = 2.0, timeout_s: Optional[float] = None):
        """Registers a service for watchdog heartbeat monitoring."""
        with self._lock:
            if name in self._services:
                logger.warning(f"Watchdog service '{name}' already registered. Resetting heartbeat.")
                self._services[name].last_heartbeat = time.time()
                return
                
            t_out = timeout_s if timeout_s is not None else self._default_timeout
            self._services[name] = MonitoredService(name, expected_interval_s, t_out)
            logger.info(f"Watchdog registered service: {name} (Interval: {expected_interval_s}s, Timeout: {t_out}s)")

    def ping(self, name: str):
        """Service calls this periodically to report healthy operation."""
        with self._lock:
            service = self._services.get(name)
            if not service:
                # Auto-register if pinged without registration (flexible API)
                self._services[name] = MonitoredService(name, 2.0, self._default_timeout)
                service = self._services[name]
                
            # Log recovery if transition occurred
            if service.state != WatchdogState.HEALTHY:
                logger.info(f"[WATCHDOG RECOVERY] Service '{name}' heartbeat restored. Transitioning to HEALTHY.")
                
            service.last_heartbeat = time.time()
            service.consecutive_missed = 0
            service.state = WatchdogState.HEALTHY

    def check_services(self) -> List[Dict[str, Any]]:
        """Scans all supervised services, flags timeouts, and executes state updates."""
        with self._lock:
            now = time.time()
            results = []
            
            for service in self._services.values():
                elapsed = now - service.last_heartbeat
                
                # Check for missed heartbeats
                if elapsed > service.expected_interval_s:
                    service.consecutive_missed = int(elapsed // service.expected_interval_s)
                else:
                    service.consecutive_missed = 0
                    
                # State transitions based on timeouts and missed count
                old_state = service.state
                
                if elapsed > service.timeout_s:
                    if service.consecutive_missed >= self._fail_misses:
                        service.state = WatchdogState.FAILED
                    elif service.consecutive_missed >= self._warn_misses:
                        service.state = WatchdogState.DEGRADED
                    else:
                        service.state = WatchdogState.WARNING
                else:
                    service.state = WatchdogState.HEALTHY
                    
                if old_state != service.state:
                    logger.warning(
                        f"[WATCHDOG STATE CHANGE] Service '{service.name}' transitioned from {old_state} "
                        f"to {service.state} (Missed: {service.consecutive_missed}, Elapsed: {elapsed:.2f}s)"
                    )
                    
                results.append({
                    "name": service.name,
                    "state": service.state,
                    "elapsed_s": round(elapsed, 2),
                    "missed_heartbeats": service.consecutive_missed
                })
                
            return results

    def get_service_state(self, name: str) -> Optional[str]:
        """Query the state of a specific service."""
        with self._lock:
            service = self._services.get(name)
            return service.state if service else None

    def get_diagnostics(self) -> List[Dict[str, Any]]:
        """List execution metrics for all registered watchdogs."""
        with self._lock:
            diag = []
            for s in self._services.values():
                diag.append({
                    "name": s.name,
                    "state": s.state,
                    "last_heartbeat": s.last_heartbeat,
                    "expected_interval": s.expected_interval_s,
                    "timeout_threshold": s.timeout_s,
                    "consecutive_missed": s.consecutive_missed
                })
            return diag
