"""
tests/test_circuit_breaker.py
=============================
Automated unit tests for the Circuit Breaker & Fault Isolation Framework.
"""

import sys
import time
import pytest
from unittest.mock import patch, MagicMock
from core.reliability.circuit_breaker import (
    CircuitBreakerManager, 
    CircuitBreakerState, 
    CircuitBreakerOpenException
)

@pytest.fixture(autouse=True)
def mock_config():
    with patch('core.reliability.circuit_breaker.config') as mock_config:
        mock_config.get.side_effect = lambda key, default=None: {
            "performance.circuit_breaker.failure_threshold": 3,
            "performance.circuit_breaker.reset_timeout_s": 0.5,
            "performance.circuit_breaker.half_open_max_calls": 1,
        }.get(key, default)
        yield mock_config

@pytest.fixture(autouse=True)
def reset_manager():
    """Reset the singleton instance before each test."""
    CircuitBreakerManager._instance = None
    yield
    CircuitBreakerManager._instance = None

def test_circuit_breaker_registration():
    manager = CircuitBreakerManager()
    cb = manager.register_service("test_service")
    
    assert cb.service_name == "test_service"
    assert cb.failure_threshold == 3
    assert cb.reset_timeout_s == 0.5
    assert cb.half_open_max_calls == 1
    assert cb.state == CircuitBreakerState.CLOSED

def test_circuit_breaker_successful_execution():
    manager = CircuitBreakerManager()
    
    @manager.protect("success_service")
    def my_service():
        return "success"
        
    result = my_service()
    assert result == "success"
    
    cb = manager.get_breaker("success_service")
    assert cb is not None
    assert cb.state == CircuitBreakerState.CLOSED
    assert cb.failure_count == 0

@patch('core.reliability.circuit_breaker.RecoveryEngine')
def test_circuit_breaker_trips_to_open(mock_recovery_engine):
    manager = CircuitBreakerManager()
    
    mock_engine_instance = MagicMock()
    mock_recovery_engine.return_value = mock_engine_instance

    @manager.protect("failing_service")
    def my_service():
        raise ValueError("Simulated failure")
        
    cb = manager.register_service("failing_service", failure_threshold=2)

    # First failure
    with pytest.raises(ValueError):
        my_service()
    assert cb.state == CircuitBreakerState.CLOSED
    assert cb.failure_count == 1
    
    # Second failure - should trip to OPEN
    with pytest.raises(ValueError):
        my_service()
    assert cb.state == CircuitBreakerState.OPEN
    assert cb.failure_count == 2
    
    # Verify Recovery Engine was triggered
    mock_engine_instance.trigger_recovery.assert_called_once_with("failing_service")
    
    # Third call - should immediately reject without executing
    with pytest.raises(CircuitBreakerOpenException):
        my_service()

def test_circuit_breaker_half_open_and_recovery():
    manager = CircuitBreakerManager()
    
    # Use a mock counter to track actual executions
    executions = {"count": 0}
    
    @manager.protect("timeout_service")
    def my_service(fail=True):
        executions["count"] += 1
        if fail:
            raise ValueError("Simulated failure")
        return "success"
        
    cb = manager.register_service("timeout_service", failure_threshold=1, reset_timeout_s=0.2, half_open_max_calls=1)
    
    # Trip the breaker
    with pytest.raises(ValueError):
        my_service(fail=True)
    assert cb.state == CircuitBreakerState.OPEN
    assert executions["count"] == 1
    
    # Blocked call
    with pytest.raises(CircuitBreakerOpenException):
        my_service(fail=True)
    assert executions["count"] == 1 # Did not execute
    
    # Wait for timeout
    time.sleep(0.3)
    
    # Now it should allow ONE execution in HALF_OPEN state
    # We will let it fail again to see it go back to OPEN
    with pytest.raises(ValueError):
        my_service(fail=True)
        
    assert executions["count"] == 2
    assert cb.state == CircuitBreakerState.OPEN
    
    # Wait again
    time.sleep(0.3)
    
    # Now it should allow ONE execution in HALF_OPEN state
    # We will succeed this time to see it go back to CLOSED
    result = my_service(fail=False)
    assert result == "success"
    assert executions["count"] == 3
    assert cb.state == CircuitBreakerState.CLOSED
    assert cb.failure_count == 0

def test_diagnostics():
    manager = CircuitBreakerManager()
    cb1 = manager.register_service("service1")
    cb2 = manager.register_service("service2", failure_threshold=1)
    
    cb2.record_failure() # Trips cb2 to OPEN
    
    diag = manager.get_diagnostics()
    assert len(diag) == 2
    
    s1_diag = next(d for d in diag if d["service_name"] == "service1")
    s2_diag = next(d for d in diag if d["service_name"] == "service2")
    
    assert s1_diag["state"] == "CLOSED"
    assert s2_diag["state"] == "OPEN"
    assert "timeout_remaining_s" in s2_diag
