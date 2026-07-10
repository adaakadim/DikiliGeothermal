# SCADA Core API Reference

## Class: `SCADAEngine`
Location: `core/engine.py`

### `read_tag(tag_name: str) -> float`
**Purpose**: Retrieves the last known value of a tag from the internal state map (does not touch network).
- **Parameters**: `tag_name` (str)
- **Returns**: `float`
- **Exceptions**: `KeyError` if tag does not exist.

### `write_tag(tag_name: str, value: float) -> bool`
**Purpose**: Pushes a new setpoint to the DAL and updates internal state.
- **Parameters**: `tag_name` (str), `value` (float)
- **Returns**: `True` if successfully propagated to hardware.

## Class: `AlarmManager`
Location: `core/alarms/alarm_manager.py`

### `trigger(alarm_id: str, severity: str) -> None`
**Purpose**: Manually forces an alarm into the `ActiveUnacknowledged` state.
- **Parameters**: `alarm_id` (str), `severity` (str: WARNING, CRITICAL).

### `acknowledge(alarm_id: str) -> None`
**Purpose**: Transitions an alarm to `ActiveAcknowledged` or `ClearedAcknowledged`.
