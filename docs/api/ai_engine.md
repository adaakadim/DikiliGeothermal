# AI Engine API Reference

## Class: `AIEngine`
Location: `core/ai/ai_engine.py`

### `analyze(tag_name: str, data_array: list) -> float`
**Purpose**: Runs a batch inference over a window of historical data.
- **Parameters**: 
  - `tag_name` (str)
  - `data_array` (list): Time-series floats.
- **Returns**: `float` (Anomaly confidence score 0.0-1.0).
