"""
core/auth/auth.py
=================
Authentication and Authorization stub for Dikili Geothermal SCADA.
Provides user roles and permission checks.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class Role(Enum):
    ADMINISTRATOR = "Administrator"
    ENGINEER = "Engineer"
    OPERATOR = "Operator"
    VIEWER = "Viewer"

@dataclass
class User:
    username: str
    role: Role

class AuthManager:
    """
    Manages current logged in user and permissions.
    """

    def __init__(self):
        # By default, we simulate an Engineer logged in for HMI demo purposes.
        self._current_user: Optional[User] = User(username="default_engineer", role=Role.ENGINEER)

    def login(self, username: str, password_hash: str) -> bool:
        """
        Authenticate a user. (Stub implementation)
        """
        logger.info(f"AuthManager: Attempting login for {username} (STUB)")
        # In a real scenario, this connects to Active Directory or a database.
        return True

    def logout(self) -> None:
        if self._current_user:
            logger.info(f"AuthManager: {self._current_user.username} logged out.")
        self._current_user = None

    def get_current_user(self) -> Optional[User]:
        return self._current_user

    def has_permission(self, required_role: Role) -> bool:
        """
        Check if the current user meets the required role level.
        Role hierarchy: Administrator > Engineer > Operator > Viewer
        """
        if not self._current_user:
            return False
        
        hierarchy = [Role.VIEWER, Role.OPERATOR, Role.ENGINEER, Role.ADMINISTRATOR]
        current_level = hierarchy.index(self._current_user.role)
        required_level = hierarchy.index(required_role)
        
        return current_level >= required_level
