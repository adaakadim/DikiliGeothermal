"""
tests/test_orchestrator.py
==========================
Automated unit tests for Health Check & Service Orchestrator Framework.
"""

import sys
from unittest.mock import MagicMock

# Mock optional packages to run tests without HMI plotting requirements
sys.modules['matplotlib'] = MagicMock()
sys.modules['matplotlib.pyplot'] = MagicMock()
sys.modules['matplotlib.animation'] = MagicMock()
sys.modules['matplotlib.gridspec'] = MagicMock()
sys.modules['matplotlib.lines'] = MagicMock()
sys.modules['matplotlib.backends'] = MagicMock()
sys.modules['matplotlib.backends.backend_tkagg'] = MagicMock()
sys.modules['pandas'] = MagicMock()

import pytest
from core.reliability.service_orchestrator import ServiceOrchestrator, ServiceState

@pytest.fixture(autouse=True)
def reset_orchestrator():
    ServiceOrchestrator._instance = None
    yield
    ServiceOrchestrator._instance = None

def test_service_registration():
    orchestrator = ServiceOrchestrator()
    
    # Register dummy service
    orchestrator.register_service("telemetry", lambda: True)
    
    summary = orchestrator.get_health_summary()
    assert summary["total_services"] == 1
    
    # Duplicate registration error
    with pytest.raises(ValueError, match="Duplicate service registration"):
        orchestrator.register_service("telemetry", lambda: True)

def test_health_checks_status_transitions():
    orchestrator = ServiceOrchestrator()
    
    # 1. ONLINE check
    orchestrator.register_service("watchdog", lambda: True)
    res = orchestrator.execute_health_check("watchdog")
    assert res["status"] == ServiceState.ONLINE
    assert res["health_score"] == 100.0
    
    # 2. Transition to OFFLINE check on exception
    def failing_action():
        raise RuntimeError("Connection Timeout")
        
    orchestrator.register_service("plc_comm", failing_action)
    res_fail = orchestrator.execute_health_check("plc_comm")
    assert res_fail["status"] == ServiceState.OFFLINE
    assert res_fail["health_score"] == 75.0 # drops by 25
    assert "Timeout" in res_fail["last_error"]
    
    # Verify failed list
    failed = orchestrator.get_failed_services()
    assert len(failed) == 1
    assert failed[0]["name"] == "plc_comm"
