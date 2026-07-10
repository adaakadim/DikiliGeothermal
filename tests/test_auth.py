"""
tests/test_auth.py
===================
Automated unit tests for the Enterprise Authentication Subsystem.
"""

import time
import pytest
from core.configuration import config
from security.user import register_user, get_user, hash_password
from security.session_manager import SessionManager
from security.authentication import AuthenticationService

def test_password_hashing():
    # Test hashing derives same hash for same password and salt
    pwd = "securepassword"
    key1, salt1 = hash_password(pwd)
    key2, salt2 = hash_password(pwd, salt1)
    
    assert key1 == key2
    assert salt1 == salt2
    
    # Different salt should yield different hash
    key3, salt3 = hash_password(pwd)
    assert key1 != key3

def test_user_registration():
    username = "test_user"
    password = "testpassword123"
    user = register_user(username, password)
    
    assert user.username == username
    assert user.salt is not None
    assert user.password_hash != password.encode('utf-8')
    
    fetched = get_user(username)
    assert fetched == user

def test_authentication_service():
    auth_service = AuthenticationService()
    
    # Test successful auth
    sess = auth_service.authenticate("dikili", "jeo123")
    assert sess is not None
    assert sess.username == "dikili"
    assert sess.session_id is not None
    
    # Clean up session
    auth_service.session_manager.terminate_session(sess.session_id)

def test_login_attempts_lockout():
    auth_service = AuthenticationService()
    username = "lockout_user"
    register_user(username, "pass")
    
    max_attempts = config.get("security.max_login_attempts", 3)
    
    # Try invalid password max_attempts times
    for i in range(max_attempts):
        sess = auth_service.authenticate(username, "wrongpass")
        assert sess is None
        
    # Check if locked out
    assert username in auth_service._locked_users
    
    # Try correct password while locked out
    sess = auth_service.authenticate(username, "pass")
    assert sess is None
    
    # Unlock and verify success
    auth_service.unlock_user(username)
    assert username not in auth_service._locked_users
    sess = auth_service.authenticate(username, "pass")
    assert sess is not None
    auth_service.session_manager.terminate_session(sess.session_id)

def test_session_expiration():
    sm = SessionManager()
    sess = sm.create_session("temp_user")
    
    # Mock timeout temporarily in the configuration
    config.set("security.session_timeout_sec", 1) # 1 second
    
    # Active right now
    assert sm.validate_session(sess.session_id) is True
    
    # Wait for timeout
    time.sleep(1.2)
    
    # Should be invalid and automatically cleaned up
    assert sm.validate_session(sess.session_id) is False
    assert sm.get_session(sess.session_id) is None
    
    # Restore configuration
    config.set("security.session_timeout_sec", 900)
