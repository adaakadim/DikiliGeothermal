"""
tests/test_scheduler.py
=======================
Automated unit tests for the Enterprise Scheduler and background task workers.
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
from core.scheduler.enterprise_scheduler import EnterpriseScheduler, TaskPriority

@pytest.fixture(autouse=True)
def cleanup_scheduler():
    # Make sure we reset the singleton before and after each test
    EnterpriseScheduler._instance = None
    yield
    EnterpriseScheduler._instance = None

def test_task_registration():
    scheduler = EnterpriseScheduler()
    
    counter = [0]
    def task_action():
        counter[0] += 1
        
    scheduler.register_task(
        name="test_periodic",
        action=task_action,
        interval=0.1,
        priority=TaskPriority.HIGH
    )
    
    # Assert registration
    diag = scheduler.get_diagnostics()
    assert len(diag) == 1
    assert diag[0]["name"] == "test_periodic"
    assert diag[0]["priority"] == "HIGH"

def test_duplicate_task_registration():
    scheduler = EnterpriseScheduler()
    
    scheduler.register_task("dup", lambda: None, 1.0)
    
    with pytest.raises(ValueError, match="Duplicate task registration"):
        scheduler.register_task("dup", lambda: None, 2.0)

def test_scheduler_thread_execution():
    scheduler = EnterpriseScheduler()
    
    counter = [0]
    def task_action():
        counter[0] += 1
        
    scheduler.register_task(
        name="run_task",
        action=task_action,
        interval=0.01,
        priority=TaskPriority.HIGH
    )
    
    # Start background executor
    scheduler.start()
    
    # Sleep to allow execution ticks
    time.sleep(0.08)
    
    # Shutdown worker thread
    scheduler.shutdown()
    
    assert counter[0] > 0
    
    diag = scheduler.get_diagnostics()
    assert diag[0]["execution_count"] == counter[0]
    assert diag[0]["failure_count"] == 0
