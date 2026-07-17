# Developer Guide

## Architecture Overview
The SCADA platform enforces strict Separation of Concerns (SoC) and utilizes Dependency Injection patterns to maintain testability.
- **`core/`**: System foundations, logging, configuration management, and drivers (Modbus/OPC-UA).
- **`simulation/`**: The deterministic physics engine. Modifications here should be heavily verified against thermodynamic laws.
- **`scada/`**: The middleware bridging sensor models with the tag database, historians, and alarm engines.
- **`analytics/`**: All scikit-learn models, predictive maintenance equations, and SHAP explainers.
- **`hmi/` & `gui/`**: The presentation layer. Widgets are written in `tkinter` using `ttk` styles.

## Coding Standards
1. **Typing**: Use PEP 484 type hints for all function signatures.
2. **ISA-101**: UI updates must adhere to High-Performance HMI standards. Avoid bright, saturated colors unless representing a critical unacknowledged alarm.
3. **Threading**: Tkinter is NOT thread-safe. All long-running Historian writes or AI inferences must occur in background loops or use `.after()` queuing mechanisms to prevent locking the main GUI.

## Extension Guide
To add a new AI model:
1. Implement the logic in `analytics/ai/`.
2. Map the DTO (Data Transfer Object) in `scada/event_engine.py`.
3. Register the new visualization panel in `hmi/main_window.py` under the `self._panels` dictionary.
