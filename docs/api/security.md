# Security API Reference

## Class: `AuthManager`
Location: `core/security/auth.py`

### `login(username: str, password_hash: str) -> str`
**Purpose**: Authenticates an operator.
- **Returns**: `str` (JWT session token).
- **Exceptions**: `PermissionError` on failure.

### `has_permission(session_token: str, action: str) -> bool`
**Purpose**: Checks RBAC policies.
- **Parameters**: `session_token` (str), `action` (str: e.g., "WRITE_TAG").
