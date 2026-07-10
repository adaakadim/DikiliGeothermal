# Human-Machine Interface (HMI)

## Purpose
The primary visual presentation layer for operators to interact with the DikiliGeothermal plant. It visualizes data, captures user commands, and organizes alarm responses.

## Scope
Strictly handles User Experience (UX), layout generation, and ISA-101/ISA-18.2 compliance graphics. It contains no core SCADA business logic or hardware communication protocols.

## Inputs & Outputs
- **Inputs:** State updates from the SCADA core, user clicks/inputs.
- **Outputs:** Command requests routed to the SCADA Core Engine.

## Dependencies
- `core/hmi/layout_engine.py`
- `core/hmi/alarm_manager_ui.py`
- `core/hmi/workspace_manager.py`

## Usage Example
```python
layout = layout_engine.generate_dashboard(user_role="OPERATOR")
```

## Future Extensions
Integration with WebSocket servers for rendering the HMI purely via a web browser using React/Vue.js instead of a native desktop framework.
