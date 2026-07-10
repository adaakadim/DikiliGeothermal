# Dikili Geothermal SCADA & Digital Twin
## Enterprise Deployment Architecture (Phase 5.4)

### Overview
This document outlines the architecture of the Dikili Geothermal project, a comprehensive industrial control system incorporating a SCADA backend, an AI Predictive Maintenance engine, a live Digital Twin, and a Professional HMI. 

In Phase 5.4, the system has been refactored for enterprise deployment, separating the core application logic from the data sources and introducing modular components for connectivity, configuration, databasing, and authentication.

---

### Core Architecture Layers

#### 1. Connectivity Layer (`core/connectivity`)
The `IDataProvider` interface abstracts the physical or simulated data source. 
- **Current Integration**: `SimulatorDataProvider` runs the internal physics engine.
- **Future Integration**: Stubs for `OPCUADataProvider`, `ModbusTCPDataProvider`, `MQTTDataProvider`, and `RESTDataProvider` are ready to be implemented for physical PLC connectivity.

#### 2. Configuration Management (`core/config`)
`SystemConfig` provides a centralized configuration hub, loading parameters from `data/config/system_config.json`. It defines process limits, AI thresholds, logging levels, and communication endpoints.

#### 3. Data Historian (`core/historian`)
`DataHistorian` is a SQLite-based database (`data/historian.db`) designed for efficient querying and long-term storage of:
- Sensor Readings (Temp, Pressure, Flow)
- AI Predictions & Health Scores
- Process Alarms & Events

#### 4. Security & Roles (`core/auth`)
`AuthManager` handles role-based access control (RBAC). Currently simulated, this module is structured to connect to Active Directory or an external Identity Provider, supporting Administrator, Engineer, Operator, and Viewer roles.

#### 5. Diagnostics (`core/diagnostics`)
`DiagnosticsService` monitors system health, tracking CPU and Memory usage via `psutil`, along with internal latencies and subsystem statuses (AI, Comms, DB, Sim).

#### 6. Logging (`core/logging`)
Standardized Python `logging` with `RotatingFileHandler` ensures all critical system events are captured in `logs/system.log` and `logs/error.log` without consuming excessive disk space.

---

### Data Flow Pipeline

1. **Acquisition**: HMI requests data via `IDataProvider.read_all()`.
2. **Historization**: Raw readings are saved to SQLite via `DataHistorian`.
3. **AI Evaluation**: `FaultDetector` and `predict_plant_state` evaluate the data for anomalies.
4. **Digital Twin Sync**: AI results and raw data update the `DikiliFacility` model.
5. **Visualization**: `gui.app` renders the updated SCADA dashboard, Process Diagram, and Diagnostics panel.
