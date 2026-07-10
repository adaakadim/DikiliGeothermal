# Digital Twin Simulator

## Purpose
A pure physics-based execution layer that perfectly mimics the thermodynamic properties of the Dikili Geothermal Plant.

## Scope
Validates HMI graphics, tests AI predictive models, and trains operators by generating realistic synthetic plant data. It does not interact with physical PLC networks.

## Inputs & Outputs
- **Inputs:** Operator setpoints (simulated valves/pumps).
- **Outputs:** Thermodynamic output responses (temperature curves, pressure drops).

## Dependencies
- `core/drivers/simulation_driver.py`
- `core/physics/thermo_models.py` (Future Integration)

## Usage Example
```python
# Typically loaded automatically when APP_ENV=simulation
```

## Future Extensions
Integration with 3D WebGL renderers for spatial temperature mapping inside the HMI.
