"""
tests/test_recovery.py
======================
Automated unit tests for Auto-Recovery Engine Framework.
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
from core.reliability.recovery_engine import RecoveryEngine, RecoveryState, RecoveryPolicyType

@pytest.fixture(autouse=True)
def reset_recovery():
    RecoveryEngine._instance = None
    yield
    RecoveryEngine._instance = None

def test_recovery_registration():
    engine = RecoveryEngine()
    
    # Register dummy recovery
    engine.register_policy("opc_comm", RecoveryPolicyType.RESET_STATE, lambda: True)
    
    assert engine.get_recovery_state("opc_comm") == RecoveryState.IDLE
    
    diag = engine.get_diagnostics()
    assert len(diag) == 1
    assert diag[0]["service_name"] == "opc_comm"
    assert diag[0]["policy_type"] == RecoveryPolicyType.RESET_STATE

def test_recovery_success_flow():
    engine = RecoveryEngine()
    
    counter = [0]
    def mock_recovery():
        counter[0] += 1
        return True
        
    engine.register_policy("ai_predictor", RecoveryPolicyType.REINITIALIZE_MODULE, mock_recovery)
    
    state = engine.trigger_recovery("ai_predictor")
    assert state == RecoveryState.RECOVERED
    assert counter[0] == 1

def test_recovery_retry_escalation():
    engine = RecoveryEngine()
    
    # Register failing callback
    engine.register_policy("db_historian", RecoveryPolicyType.LOG_ONLY, lambda: False)
    
    # Trigger 1st retry
    state1 = engine.trigger_recovery("db_historian")
    assert state1 != RecoveryState.RECOVERED
    
    # Clear cooldown to bypass time restriction for testing retries
    policy = engine._policies["db_historian"]
    policy.cooldown_expires = 0.0
    
    # 2nd retry
    engine.trigger_recovery("db_historian")
    policy.cooldown_expires = 0.0
    
    # 3rd retry
    engine.trigger_recovery("db_historian")
    policy.cooldown_expires = 0.0
    
    # 4th trigger: exceeds limit (max_retries = 3)
    state_final = engine.trigger_recovery("db_historian")
    assert state_final == RecoveryState.ESCALATED
