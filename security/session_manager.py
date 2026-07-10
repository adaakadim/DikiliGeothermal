"""
security/session_manager.py
===========================
Handles SCADA session tracking, activity timeouts, and cleanup.
"""

import time
import secrets
import logging
from dataclasses import dataclass
from typing import Dict, Optional
from core.configuration import config

logger = logging.getLogger(__name__)

@dataclass
class Session:
    session_id: str
    username: str
    login_time: float
    last_activity: float

class SessionManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._instance._sessions = {}
        return cls._instance

    def create_session(self, username: str) -> Session:
        """Create a new session with a secure random session ID."""
        session_id = secrets.token_hex(32)
        now = time.time()
        session = Session(
            session_id=session_id,
            username=username,
            login_time=now,
            last_activity=now
        )
        self._sessions[session_id] = session
        logger.info(f"Session created for user: {username} (ID: {session_id[:8]}...)")
        return session

    def validate_session(self, session_id: str) -> bool:
        """
        Verify if the session exists and has not expired.
        Updates the last activity timestamp if active.
        """
        self.cleanup_expired_sessions()
        
        session = self._sessions.get(session_id)
        if not session:
            return False
            
        # Update last activity
        session.last_activity = time.time()
        return True

    def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve a session by ID if valid."""
        if self.validate_session(session_id):
            return self._sessions.get(session_id)
        return None

    def terminate_session(self, session_id: str):
        """Remove a session from tracking."""
        if session_id in self._sessions:
            session = self._sessions.pop(session_id)
            logger.info(f"Session terminated for user: {session.username}")

    def cleanup_expired_sessions(self):
        """Iterate through active sessions and remove any that have exceeded the timeout limit."""
        now = time.time()
        # Retrieve timeout config (default to 900 seconds / 15 minutes)
        timeout_sec = config.get("security.session_timeout_sec", 900)
        
        expired_ids = []
        for sid, sess in self._sessions.items():
            if now - sess.last_activity > timeout_sec:
                expired_ids.append(sid)
                
        for sid in expired_ids:
            sess = self._sessions.pop(sid)
            logger.warning(f"Session expired due to inactivity: {sess.username} (Timeout: {timeout_sec}s)")
            # Route an error event or trigger log notifications
