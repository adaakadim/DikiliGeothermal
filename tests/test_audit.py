"""
tests/test_audit.py
===================
Automated unit tests for the Security Audit Trail framework.
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

import os
import json
from pathlib import Path
import pytest
from core.logging.logger_setup import setup_logging
from security.audit import AuditLogger
from security.authentication import AuthenticationService
from security.user import register_user

LOG_FILE = Path("logs/security_audit.log")

@pytest.fixture(autouse=True)
def setup_test_logging():
    # Make sure logging is initialized and the log dir exists
    setup_logging("INFO")
    if LOG_FILE.exists():
        # Clear log file content before each test
        open(LOG_FILE, "w").close()
    yield

def read_last_audit_line() -> dict:
    assert LOG_FILE.exists()
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        if not lines:
            return {}
        # The logging framework format prefixes the message, e.g.:
        # 2026-07-09 09:45:55 [INFO] security.audit - {"timestamp": ...}
        # We need to extract the JSON payload.
        last_line = lines[-1].strip()
        json_start = last_line.find("{")
        if json_start == -1:
            return {}
        return json.loads(last_line[json_start:])

def test_audit_generation():
    AuditLogger.log_event(
        action="User Login",
        module="security.auth",
        result="SUCCESS",
        severity="INFO",
        username="dikili",
        session_id="sess_12345",
        details="Logged in via GUI"
    )
    
    record = read_last_audit_line()
    assert record["action"] == "User Login"
    assert record["module"] == "security.auth"
    assert record["result"] == "SUCCESS"
    assert record["severity"] == "INFO"
    assert record["username"] == "dikili"
    assert record["session_id"] == "sess_12345"
    assert record["details"] == "Logged in via GUI"
    assert "timestamp" in record

def test_audit_missing_session():
    # Test fallback to SYSTEM and NO_SESSION
    AuditLogger.log_event(
        action="System Boot",
        module="core.startup",
        result="SUCCESS",
        severity="INFO"
    )
    
    record = read_last_audit_line()
    assert record["username"] == "SYSTEM"
    assert record["session_id"] == "NO_SESSION"
    assert record["action"] == "System Boot"

def test_authentication_audit_integration():
    auth_service = AuthenticationService()
    
    # 1. Failed Login Audit
    sess = auth_service.authenticate("dikili", "wrong_password")
    assert sess is None
    
    record = read_last_audit_line()
    assert record["action"] == "Login"
    assert record["result"] == "FAIL"
    assert record["username"] == "dikili"
    assert "wrong" in record["details"] or "Failed" in record["details"]

    # 2. Successful Login Audit
    sess2 = auth_service.authenticate("dikili", "jeo123")
    assert sess2 is not None
    
    record = read_last_audit_line()
    assert record["action"] == "Login"
    assert record["result"] == "SUCCESS"
    assert record["username"] == "dikili"
    assert record["session_id"] == sess2.session_id
    
    auth_service.session_manager.terminate_session(sess2.session_id)
