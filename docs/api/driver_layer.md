# Driver Abstraction Layer (DAL) API Reference

## Class: `BaseDriver`
Location: `core/drivers/base_driver.py`

### `connect() -> bool`
**Purpose**: Establishes the physical connection to the external PLC, Edge node, or Broker.
- **Parameters**: None. Configuration is injected via `__init__`.
- **Returns**: `True` if successful, `False` otherwise.
- **Exceptions**: `ConnectionError` if network is unreachable.
- **Example**:
  ```python
  driver.connect()
  ```

### `disconnect() -> None`
**Purpose**: Safely tears down the network socket and stops internal threading daemons.

### `read_tag(logical_tag: str) -> float`
**Purpose**: Synchronously polls a specific tag.
- **Parameters**: 
  - `logical_tag` (str): The logical SCADA tag (e.g., `"W01.Pressure"`).
- **Returns**: `float` representing the tag value.
- **Exceptions**: `ValueError` if the tag is unmapped. `ConnectionError` if the driver is OFFLINE.

### `write_tag(logical_tag: str, value: float) -> bool`
**Purpose**: Synchronously writes a value to a physical PLC.
- **Parameters**:
  - `logical_tag` (str): The logical SCADA tag.
  - `value` (float): The value to write.
- **Exceptions**: `ValueError` if tag is read-only.
