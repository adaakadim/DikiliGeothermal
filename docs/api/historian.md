# Historian API Reference

## Class: `Historian`
Location: `core/historian/historian.py`

### `log_value(tag_name: str, value: float, timestamp: int = None) -> None`
**Purpose**: Buffers a tag value into memory for asynchronous disk flushing.
- **Parameters**: 
  - `tag_name` (str)
  - `value` (float)
  - `timestamp` (int): Optional Unix epoch. If None, current time is used.
- **Exceptions**: None. Silently buffers.

### `query(tag_name: str, start_time: int, end_time: int) -> list`
**Purpose**: Retrieves a historical array of values for UI plotting or AI training.
- **Returns**: `list` of dictionaries `[{"timestamp": 123, "value": 85.0}]`
