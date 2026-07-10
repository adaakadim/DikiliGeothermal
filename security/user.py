"""
security/user.py
================
Represents user records and provides secure PBKDF2 password hashing.
"""

import hashlib
import secrets
from dataclasses import dataclass
from typing import Dict

@dataclass
class User:
    username: str
    password_hash: bytes
    salt: bytes

# In-memory database of registered users for demonstration/SCADA purposes.
# In production, this would load from a secure file or query Active Directory.
_user_registry: Dict[str, User] = {}

def hash_password(password: str, salt: bytes = None) -> tuple[bytes, bytes]:
    """
    Derive a secure key using PBKDF2-HMAC-SHA256 with 100,000 iterations.
    Returns: (key_hash, salt)
    """
    if salt is None:
        salt = secrets.token_bytes(16)
    # We use a high iteration count to protect against brute-force attacks.
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return key, salt

def register_user(username: str, password: str) -> User:
    """Register a new user, hash the password, and store in the registry."""
    key_hash, salt = hash_password(password)
    user = User(username=username, password_hash=key_hash, salt=salt)
    _user_registry[username] = user
    return user

def get_user(username: str) -> User | None:
    """Retrieve a user from the registry by username."""
    return _user_registry.get(username)

# Pre-register default SCADA users
register_user("dikili", "jeo123")

