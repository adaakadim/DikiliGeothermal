# SCADA Core Engine

## Purpose
The primary execution engine that routes tag values, triggers alarms, and manages the central state of the DikiliGeothermal platform.

## Scope
Serves as the central nervous system. It does not communicate with hardware directly (delegated to the DAL) nor render graphics (delegated to the HMI). It strictly holds state and fires business logic.

## Inputs & Outputs
- **Inputs:** Raw telemetry via the Driver Abstraction Layer, operator setpoints from the HMI.
- **Outputs:** State changes broadcast to the Historian and HMI; Alarm events pushed to the Alarm Manager.

## Dependencies
- `core/drivers/driver_manager.py` (DAL)
- `core/historian/historian.py`

## Usage Example
```python
from core.engine import SCADAEngine
engine = SCADAEngine()
val = engine.read_tag("W01.Pressure")
```

## Future Extensions
Implementation of a distributed Redundant Core (Active/Standby) using a heartbeating mechanism across multiple VMs.
