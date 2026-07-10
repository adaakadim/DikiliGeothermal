# Historian Pipeline

## Purpose
A high-performance time-series data storage and retrieval engine designed to log tag values across the entire lifecycle of the Dikili Geothermal Plant.

## Scope
Manages in-memory buffering, asynchronous disk flushing, and fast querying. It strictly decouples storage execution from the main SCADA thread to ensure logging never stalls real-time operations.

## Inputs & Outputs
- **Inputs:** High-frequency tag updates from the DAL or SCADA Core.
- **Outputs:** Time-series arrays, aggregated window averages, and raw disk writes (Parquet/CSV format).

## Dependencies
- `core/engine.py`
- (Future) `pandas` / `pyarrow` for fast Parquet persistence.

## Usage Example
```python
historian.log_value("W01.Temperature", 85.0, timestamp=17000000)
data = historian.query("W01.Temperature", start_time, end_time)
```

## Future Extensions
Integration with enterprise time-series databases like InfluxDB or TimescaleDB for cloud-based long-term retention.
