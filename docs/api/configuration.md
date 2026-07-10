# Configuration System API Reference

## Class: `ConfigManager`
Location: `core/configuration.py`

### `get_config() -> SystemConfig`
**Purpose**: Retrieves the globally validated configuration dataclass based on the `APP_ENV` environment variable.
- **Returns**: `SystemConfig` object.
- **Exceptions**: `ValueError` if `APP_ENV` is unrecognized.
