"""
security/authentication.py
==========================
Service orchestrating login validation, password checking, and attempts lockout.
"""

import logging
from typing import Optional
from core.configuration import config
from security.user import get_user, hash_password
from security.session_manager import SessionManager, Session

logger = logging.getLogger(__name__)

class AuthenticationService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AuthenticationService, cls).__new__(cls)
            cls._instance._attempts = {}
            cls._instance._locked_users = set()
            cls._instance.session_manager = SessionManager()
        return cls._instance

    def authenticate(self, username: str, password: str) -> Optional[Session]:
        """
        Authenticate a user.
        Checks lockouts, hashes input, validates passwords, and resets attempts upon success.
        """
        from security.audit import AuditLogger
        max_attempts = config.get("security.max_login_attempts", 3)
        
        if username in self._locked_users:
            logger.error(f"Failed login attempt: Account locked for user '{username}'.")
            AuditLogger.log_event("Login", "security.auth", "FAIL_LOCKED", "WARN", username, details="Account is locked")
            return None

        user = get_user(username)
        if not user:
            self._record_failed_attempt(username, max_attempts)
            return None

        # Verify password
        input_hash, _ = hash_password(password, user.salt)
        if input_hash != user.password_hash:
            self._record_failed_attempt(username, max_attempts)
            return None

        # Reset failed attempts on success
        self._attempts[username] = 0
        
        # Create session
        session = self.session_manager.create_session(username)
        logger.info(f"Successful login: User '{username}' logged in.")
        AuditLogger.log_event("Login", "security.auth", "SUCCESS", "INFO", username, session.session_id)
        return session

    def _record_failed_attempt(self, username: str, max_attempts: int):
        """Track and escalate failed login attempts."""
        from security.audit import AuditLogger
        self._attempts[username] = self._attempts.get(username, 0) + 1
        attempts = self._attempts[username]
        logger.warning(f"Failed login: User '{username}' entered invalid credentials (Attempt {attempts}/{max_attempts}).")
        AuditLogger.log_event("Login", "security.auth", "FAIL", "WARN", username, details=f"Failed attempt {attempts}/{max_attempts}")
        
        if attempts >= max_attempts:
            self._locked_users.add(username)
            logger.critical(f"Account locked: User '{username}' locked out due to {attempts} failed attempts.")
            AuditLogger.log_event("Lockout", "security.auth", "LOCK", "CRIT", username, details=f"Locked out after {attempts} failed attempts")

    def unlock_user(self, username: str):
        """Administrative unlock helper."""
        from security.audit import AuditLogger
        if username in self._locked_users:
            self._locked_users.remove(username)
            self._attempts[username] = 0
            logger.info(f"Account unlocked: User '{username}' unlocked by administrator.")
            AuditLogger.log_event("Unlock", "security.auth", "SUCCESS", "INFO", username, details="Unlocked by administrator")
