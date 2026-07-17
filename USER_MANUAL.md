# User Manual

## Overview
The Dikili Geothermal SCADA platform provides a centralized hub for monitoring, controlling, and analyzing the physics of a thermodynamic wellfield.

## Panels & Features

### 1. Mission Control
The primary executive dashboard displaying high-level financial, energy, and risk metrics. It aggregates plant health into a single unified score.

### 2. Operator Dashboard
Live P&ID (Piping and Instrumentation Diagram) data showing real-time flows, temperatures, and pressures of individual production wells.

### 3. Alarm Center
Automatically logs and highlights variables that breach safe operating boundaries. The ISA-101 alarm methodology assigns colors based on priority (Red = Critical, Yellow = Warning).

### 4. Scenario Manager
Allows operators to instantly switch the mathematical state of the plant. Predefined scenarios include:
- Summer / Winter Operations
- Pump Failure Simulation
- Maintenance Mode
- Emergency Shutdown

### 5. AI Operator Assistant
Constantly monitors the SCADA stream for hidden, non-linear faults. It issues English-language recommendations if it predicts an imminent failure.

### 6. Predictive Maintenance (RUL)
Uses historical degradation curves to estimate the Remaining Useful Life of critical pumps and heat exchangers, aiding in preventative overhaul scheduling.

### 7. Digital Twin
A physical simulator running in parallel to the real plant, allowing operators to detect deviations between expected and actual thermodynamic outputs.

### 8. Configuration Center
Located under the Engineering tab. Authorized personnel can modify Historian batch sizes, Alarm setpoints, and Simulation intervals dynamically. Invalid data is automatically rejected by the validation engine.
