"""
tests/test_watchdog.py
======================
Automated unit tests for the Enterprise Watchdog Framework.
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

import time
import pytest
from core.reliability.watchdog import WatchdogEngine, WatchdogState

@pytest.fixture(autouse=True)
def reset_watchdog():
    WatchdogEngine._instance = None
    yield
    WatchdogEngine._instance = None

def test_watchdog_registration_and_ping():
    engine = WatchdogEngine()
    
    # Register service
    engine.register_service("scada_engine", expected_interval_s=1.0, timeout_s=3.0)
    
    assert engine.get_service_state("scada_engine") == WatchdogState.HEALTHY
    
    # Ping
    time.sleep(0.01)
    engine.ping("scada_engine")
    
    diag = engine.get_diagnostics()
    assert len(diag) == 1
    assert diag[0]["name"] == "scada_engine"
    assert diag[0]["consecutive_missed"] == 0

def test_watchdog_timeout_transitions():
    engine = WatchdogEngine()
    
    # Register with a very short interval/timeout for testing status updates
    engine.register_service("test_service", expected_interval_s=0.01, timeout_s=0.02)
    
    # 1. Healthy state initially
    assert engine.get_service_state("test_service") == WatchdogState.HEALTHY
    
    # 2. Wait to trigger warning/degraded/failed states
    time.sleep(0.12)
    
    # Run scan
    engine.check_services()
    
    state = engine.get_service_state("test_service")
    assert state in (WatchdogState.DEGRADED, WatchdogState.FAILED)
    
    # 3. Restore state via ping
    engine.ping("test_service")
    assert engine.get_service_state("test_service") == WatchdogState.HEALTHY
