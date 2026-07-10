# AI Prediction Engine

## Purpose
Monitors real-time SCADA telemetry against historical baseline data to detect anomalous behaviors and predict equipment failures before they trigger critical ISA-18.2 alarms.

## Scope
Reads passively from the Historian and Driver Abstraction Layer. It can recommend actions to operators but is explicitly prohibited from autonomously writing commands to physical PLCs (read-only constraint).

## Inputs & Outputs
- **Inputs:** High-frequency tag telemetry, Historian arrays.
- **Outputs:** Anomaly confidence scores, predictive maintenance alerts.

## Dependencies
- `core/historian/historian.py`
- `core/drivers/driver_manager.py`
- External ML libraries (PyTorch/Scikit-Learn).

## Usage Example
```python
prediction = ai_engine.analyze_well_health("W01")
if prediction.anomaly_score > 0.85:
    raise PredictiveAlert(prediction.details)
```

## Future Extensions
Deployment of Edge ML models directly alongside MQTT brokers at the wellheads for zero-latency vibration analysis.
