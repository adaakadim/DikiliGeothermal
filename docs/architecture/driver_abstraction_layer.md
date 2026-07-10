# Driver Abstraction Layer (DAL)

## Purpose
Decouples the core SCADA application from the physical realities of industrial network protocols (Modbus TCP, OPC UA, MQTT).

## Scope
Provides a unified, strict contract (`BaseDriver`) ensuring that whether data originates from a legacy RTU or a modern IIoT edge gateway, the application layer uses identical syntax (`read_tag`, `subscribe`).

## Inputs & Outputs
- **Inputs:** Read/Write requests from the SCADA core.
- **Outputs:** Standardized data values, diagnostics metrics (latency, errors, timeouts).

## Dependencies
- `core/drivers/base_driver.py`
- Protocol-specific Python packages (`asyncua`, `pymodbus`, `paho-mqtt`).

## Usage Example
```python
driver = driver_manager.get_active_driver()
val = driver.read_tag("W01.Pressure")
```

## Future Extensions
Adding specific protocol drivers for DNP3 or BACnet as the geothermal plant expands into broader grid management.
