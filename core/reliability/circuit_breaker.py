"""
core/reliability/circuit_breaker.py
===================================
Circuit Breaker & Fault Isolation Framework.
Prevents cascading failures by isolating unstable services.
Coordinates with Recovery Engine.
"""

import time
import logging
import threading
from typing import Dict, Any, Callable, Optional
from enum import Enum
from functools import wraps

from core.configuration import config
from core.reliability.recovery_engine import RecoveryEngine

logger = logging.getLogger("core.reliability.circuit_breaker")

class CircuitBreakerState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class CircuitBreakerOpenException(Exception):
    """Exception raised when a service is called but its circuit breaker is OPEN."""
    pass

class CircuitBreaker:
    def __init__(self, service_name: str, failure_threshold: int, reset_timeout_s: float, half_open_max_calls: int):
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.reset_timeout_s = reset_timeout_s
        self.half_open_max_calls = half_open_max_calls

        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.half_open_calls = 0

        self._lock = threading.Lock()

    def record_success(self):
        with self._lock:
            if self.state == CircuitBreakerState.HALF_OPEN:
                logger.info(f"[CIRCUIT BREAKER] Service '{self.service_name}' recovered successfully. Circuit CLOSED.")
                self.state = CircuitBreakerState.CLOSED
            self.failure_count = 0
            self.half_open_calls = 0

    def record_failure(self):
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            logger.warning(f"[CIRCUIT BREAKER] Service '{self.service_name}' failed. Count: {self.failure_count}/{self.failure_threshold}")

            if self.state == CircuitBreakerState.CLOSED and self.failure_count >= self.failure_threshold:
                self._trip()
            elif self.state == CircuitBreakerState.HALF_OPEN:
                logger.warning(f"[CIRCUIT BREAKER] Service '{self.service_name}' failed in HALF_OPEN. Circuit OPEN again.")
                self._trip()

    def _trip(self):
        self.state = CircuitBreakerState.OPEN
        logger.error(f"[CIRCUIT BREAKER] Circuit OPENED for '{self.service_name}'. Isolation active.")
        
        # Coordinate with Recovery Engine
        try:
            engine = RecoveryEngine()
            engine.trigger_recovery(self.service_name)
        except Exception as e:
            logger.error(f"[CIRCUIT BREAKER] Failed to trigger Recovery Engine for '{self.service_name}': {e}")

    def can_execute(self) -> bool:
        with self._lock:
            if self.state == CircuitBreakerState.CLOSED:
                return True
                
            if self.state == CircuitBreakerState.OPEN:
                now = time.time()
                if now - self.last_failure_time >= self.reset_timeout_s:
                    logger.info(f"[CIRCUIT BREAKER] Timeout reached for '{self.service_name}'. Circuit transitioning to HALF_OPEN.")
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.half_open_calls = 0
                    return True
                return False
                
            if self.state == CircuitBreakerState.HALF_OPEN:
                if self.half_open_calls < self.half_open_max_calls:
                    self.half_open_calls += 1
                    return True
                return False

        return False

class CircuitBreakerManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CircuitBreakerManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self._breakers: Dict[str, CircuitBreaker] = {}
        
        self._default_failure_threshold = config.get("performance.circuit_breaker.failure_threshold", 3)
        self._default_reset_timeout_s = config.get("performance.circuit_breaker.reset_timeout_s", 30.0)
        self._default_half_open_max_calls = config.get("performance.circuit_breaker.half_open_max_calls", 1)
        
        self._initialized = True

    def register_service(self, service_name: str, 
                         failure_threshold: Optional[int] = None, 
                         reset_timeout_s: Optional[float] = None,
                         half_open_max_calls: Optional[int] = None) -> CircuitBreaker:
        """Registers a service for circuit breaker protection."""
        with self._lock:
            if service_name not in self._breakers:
                ft = failure_threshold if failure_threshold is not None else self._default_failure_threshold
                rt = reset_timeout_s if reset_timeout_s is not None else self._default_reset_timeout_s
                hc = half_open_max_calls if half_open_max_calls is not None else self._default_half_open_max_calls
                
                self._breakers[service_name] = CircuitBreaker(service_name, ft, rt, hc)
                logger.info(f"Registered service '{service_name}' with CircuitBreaker (ft={ft}, rt={rt}s, hc={hc}).")
            
            return self._breakers[service_name]

    def get_breaker(self, service_name: str) -> Optional[CircuitBreaker]:
        with self._lock:
            return self._breakers.get(service_name)

    def protect(self, service_name: str):
        """Decorator to protect a function execution with the circuit breaker."""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                breaker = self.get_breaker(service_name)
                
                if not breaker:
                    # If not registered, auto-register with defaults
                    breaker = self.register_service(service_name)
                    
                if not breaker.can_execute():
                    logger.warning(f"[CIRCUIT BREAKER] Execution blocked for '{service_name}' due to OPEN state.")
                    raise CircuitBreakerOpenException(f"Service '{service_name}' circuit breaker is OPEN.")
                    
                try:
                    result = func(*args, **kwargs)
                    breaker.record_success()
                    return result
                except Exception as e:
                    breaker.record_failure()
                    raise
            return wrapper
        return decorator

    def get_diagnostics(self) -> list:
        with self._lock:
            diag = []
            now = time.time()
            for name, cb in self._breakers.items():
                timeout_rem = max(0.0, cb.reset_timeout_s - (now - cb.last_failure_time)) if cb.state == CircuitBreakerState.OPEN else 0.0
                diag.append({
                    "service_name": name,
                    "state": cb.state.value,
                    "failure_count": cb.failure_count,
                    "failure_threshold": cb.failure_threshold,
                    "timeout_remaining_s": round(timeout_rem, 2)
                })
            return diag
