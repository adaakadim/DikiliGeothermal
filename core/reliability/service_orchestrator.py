"""
core/reliability/service_orchestrator.py
========================================
Service Orchestrator and Health Check Framework for monitoring major platform components.
"""

import time
import logging
import threading
from typing import Callable, Any, Dict, List, Optional

logger = logging.getLogger("core.reliability")

class ServiceState:
    ONLINE = "ONLINE"
    WARNING = "WARNING"
    OFFLINE = "OFFLINE"

class ServiceInfo:
    def __init__(self, name: str, check_callback: Callable[[], Any]):
        self.name = name
        self.check_callback = check_callback
        self.status = ServiceState.OFFLINE
        self.last_health_check = 0.0
        self.response_time = 0.0
        self.failure_count = 0
        self.last_error = ""
        self.start_time = time.time()
        self.health_score = 100.0

    @property
    def uptime(self) -> float:
        return time.time() - self.start_time

class ServiceOrchestrator:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ServiceOrchestrator, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._services: Dict[str, ServiceInfo] = {}
        self._initialized = True

    def register_service(self, name: str, check_callback: Callable[[], Any]):
        """Registers a service for health checks. Prevents duplicates."""
        with self._lock:
            if name in self._services:
                logger.error(f"Service '{name}' is already registered.")
                raise ValueError(f"Duplicate service registration: {name}")
                
            self._services[name] = ServiceInfo(name, check_callback)
            logger.info(f"Registered service for health monitoring: {name}")

    def unregister_service(self, name: str):
        """Removes a service from orchestration."""
        with self._lock:
            if name in self._services:
                del self._services[name]
                logger.info(f"Unregistered service: {name}")

    def execute_health_check(self, name: str) -> Dict[str, Any]:
        """Runs the health callback of a service and updates its status metrics."""
        service = self._services.get(name)
        if not service:
            logger.error(f"Cannot execute health check: Service '{name}' not found.")
            return {}

        start_time = time.time()
        try:
            # Check callback should return True or raise an exception
            res = service.check_callback()
            duration = time.time() - start_time
            
            service.response_time = duration
            service.last_health_check = time.time()
            
            if res is True or (isinstance(res, tuple) and res[0] is True):
                service.status = ServiceState.ONLINE
                service.last_error = ""
                # Gradual recovery of health score
                service.health_score = min(100.0, service.health_score + 10.0)
            else:
                raise ValueError("Health check returned failure status.")
                
        except Exception as e:
            duration = time.time() - start_time
            service.response_time = duration
            service.last_health_check = time.time()
            service.status = ServiceState.OFFLINE
            service.failure_count += 1
            service.last_error = str(e)
            service.health_score = max(0.0, service.health_score - 25.0)
            logger.error(f"Health check failed for service '{name}': {e}")
            
        return self._format_service_info(service)

    def execute_all(self) -> List[Dict[str, Any]]:
        """Triggers health checks for all registered services."""
        results = []
        for name in list(self._services.keys()):
            results.append(self.execute_health_check(name))
        return results

    def get_health_summary(self) -> Dict[str, Any]:
        """Compiles summary status and statistics."""
        with self._lock:
            total = len(self._services)
            online = sum(1 for s in self._services.values() if s.status == ServiceState.ONLINE)
            warning = sum(1 for s in self._services.values() if s.status == ServiceState.WARNING)
            offline = sum(1 for s in self._services.values() if s.status == ServiceState.OFFLINE)
            
            avg_score = sum(s.health_score for s in self._services.values()) / total if total > 0 else 100.0
            
            return {
                "total_services": total,
                "online_services": online,
                "warning_services": warning,
                "offline_services": offline,
                "overall_health_score": round(avg_score, 2),
                "timestamp": time.time()
            }

    def get_failed_services(self) -> List[Dict[str, Any]]:
        """List details of all services currently failing health checks."""
        with self._lock:
            failed = []
            for s in self._services.values():
                if s.status != ServiceState.ONLINE:
                    failed.append(self._format_service_info(s))
            return failed

    def _format_service_info(self, s: ServiceInfo) -> Dict[str, Any]:
        return {
            "name": s.name,
            "status": s.status,
            "last_health_check": s.last_health_check,
            "response_time_ms": round(s.response_time * 1000, 2),
            "failure_count": s.failure_count,
            "last_error": s.last_error,
            "uptime_s": round(s.uptime, 2),
            "health_score": s.health_score
        }
