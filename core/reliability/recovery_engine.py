"""
core/reliability/recovery_engine.py
===================================
Auto-Recovery Engine coordinating state recovery policies for degraded SCADA services.
"""

import time
import logging
import threading
from typing import Dict, Any, List, Optional, Callable

logger = logging.getLogger("core.reliability.recovery")

class RecoveryState:
    IDLE = "IDLE"
    DETECTED = "DETECTED"
    RECOVERY_PENDING = "RECOVERY_PENDING"
    RECOVERING = "RECOVERING"
    RECOVERED = "RECOVERED"
    FAILED = "FAILED"
    ESCALATED = "ESCALATED"

class RecoveryPolicyType:
    LOG_ONLY = "LOG_ONLY"
    NOTIFY_OPERATOR = "NOTIFY_OPERATOR"
    RESET_STATE = "RESET_STATE"
    RESTART_TASK = "RESTART_TASK"
    REINITIALIZE_MODULE = "REINITIALIZE_MODULE"
    ESCALATE_FAILURE = "ESCALATE_FAILURE"

class RecoveryPolicy:
    def __init__(self, service_name: str, policy_type: str, action_callback: Callable[[], bool]):
        self.service_name = service_name
        self.policy_type = policy_type
        self.action_callback = action_callback
        self.state = RecoveryState.IDLE
        self.attempts = 0
        self.last_attempt_time = 0.0
        self.cooldown_expires = 0.0

class RecoveryEngine:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(RecoveryEngine, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self._policies: Dict[str, RecoveryPolicy] = {}
        
        # Load configs
        from core.configuration import config
        self._max_retries = config.get("performance.recovery.max_retries", 3)
        self._default_cooldown = config.get("performance.recovery.cooldown_s", 10.0)
        self._backoff_factor = config.get("performance.recovery.backoff_factor", 2.0)
        
        self._initialized = True

    def register_policy(self, service_name: str, policy_type: str, action_callback: Callable[[], bool]):
        """Registers a recovery policy for a service."""
        with self._lock:
            self._policies[service_name] = RecoveryPolicy(service_name, policy_type, action_callback)
            logger.info(f"Registered recovery policy '{policy_type}' for service '{service_name}'")

    def unregister_policy(self, service_name: str):
        """Removes a service policy."""
        with self._lock:
            if service_name in self._policies:
                del self._policies[service_name]
                logger.info(f"Unregistered recovery policy for: {service_name}")

    def trigger_recovery(self, service_name: str) -> str:
        """Executes recovery callback on service failure, enforcing retries and backoff limits."""
        with self._lock:
            policy = self._policies.get(service_name)
            if not policy:
                logger.warning(f"No recovery policy registered for service: {service_name}")
                return RecoveryState.IDLE
                
            now = time.time()
            if now < policy.cooldown_expires:
                logger.warning(f"Recovery for '{service_name}' blocked by cooldown. Expires in {policy.cooldown_expires - now:.1f}s")
                return policy.state
                
            policy.state = RecoveryState.DETECTED
            policy.state = RecoveryState.RECOVERY_PENDING
            policy.state = RecoveryState.RECOVERING
            
            # Apply exponential backoff delay based on attempts
            backoff = policy.attempts * self._backoff_factor
            cooldown_period = self._default_cooldown + backoff
            
            policy.attempts += 1
            policy.last_attempt_time = now
            policy.cooldown_expires = now + cooldown_period
            
            if policy.attempts > self._max_retries:
                policy.state = RecoveryState.FAILED
                logger.error(f"[RECOVERY CRITICAL] Service '{service_name}' exceeded retry limit ({self._max_retries}). Escalating.")
                policy.state = RecoveryState.ESCALATED
                return policy.state
                
            logger.info(f"[RECOVERY EXECUTE] Attempt {policy.attempts}/{self._max_retries} for '{service_name}' (Policy: {policy.policy_type})")
            
            try:
                success = policy.action_callback()
                if success:
                    policy.state = RecoveryState.RECOVERED
                    policy.attempts = 0 # reset attempts on successful recovery
                    logger.info(f"[RECOVERY SUCCESS] Service '{service_name}' successfully recovered.")
                else:
                    logger.warning(f"[RECOVERY FAIL] Service '{service_name}' recovery attempt failed.")
            except Exception as e:
                logger.error(f"[RECOVERY ERROR] Service '{service_name}' exception during recovery: {e}")
                
            return policy.state

    def get_recovery_state(self, service_name: str) -> str:
        """Returns the current state of a service's recovery workflow."""
        with self._lock:
            policy = self._policies.get(service_name)
            return policy.state if policy else RecoveryState.IDLE

    def get_diagnostics(self) -> List[Dict[str, Any]]:
        """Returns diagnostic details for all registered recovery policies."""
        with self._lock:
            diag = []
            for p in self._policies.values():
                diag.append({
                    "service_name": p.service_name,
                    "policy_type": p.policy_type,
                    "state": p.state,
                    "attempts": p.attempts,
                    "last_attempt": p.last_attempt_time,
                    "cooldown_remaining_s": max(0.0, round(p.cooldown_expires - time.time(), 2))
                })
            return diag
