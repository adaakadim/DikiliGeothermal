# DikiliGeothermal Deployment Profiles & Environment Management

This document outlines the standard deployment profiles and feature configuration flags for the DikiliGeothermal SCADA platform. The platform uses a centralized `ConfigManager` to load settings, merge environment-specific overrides, and safely validate combinations to prevent runtime faults in the field.

## 1. Profiles

The environment is controlled via the `APP_ENV` environment variable. The system strictly enforces one of the following 5 profiles:

| Profile | Description | Intended Use |
| :--- | :--- | :--- |
| **`development`** | Default local engineering mode. | Building new features, debugging the UI, hot-reloading components. Simulation active. |
| **`testing`** | Automated CI/CD mode. | Running `pytest` regression suites. Memory databases are favored. Simulation active. |
| **`simulation`** | Operator training mode. | Full HMI active, but fully driven by the Digital Twin process simulator rather than real PLCs. |
| **`pilot`** | Shadow integration mode. | Connected to read-only tags from real PLCs. Used to train the AI Engine safely in parallel with legacy systems. |
| **`production`** | Live plant control mode. | Connected to PLCs with read/write capability. Simulation engine strictly disabled. |

---

## 2. Feature Toggles

Features are controlled via the `features.*` namespace in the configuration. They allow operations to enable/disable entire background services safely without branching the codebase.

| Feature Flag | Default | Description |
| :--- | :--- | :--- |
| `features.ai_engine` | `True` | Runs the predictive fault analysis and decision support hook. |
| `features.digital_twin` | `True` | Runs the Digital Twin pipeline. |
| `features.historian` | `True` | Flushes tag data to SQLite. |
| `features.scheduler` | `True` | Enables automated enterprise tasks. |
| `features.performance_monitor` | `True` | Tracks CPU/Memory overhead of the orchestrator. |
| `features.reliability_framework` | `True` | Enables the Auto-Recovery Engine and Circuit Breakers. |
| `features.security_features` | `True` | Enforces Authentication and Audit Trails. |
| `features.simulation_engine` | `False` | Forces the use of the physics simulator instead of external comms. |
| `features.opcua_driver` | `False` | Enables OPC UA driver (Future). |
| `features.modbus_driver` | `False` | Enables Modbus TCP driver (Future). |
| `features.mqtt_driver` | `False` | Enables MQTT driver (Future). |

---

## 3. Deployment Validation Rules

The `ConfigManager.validate_deployment()` routine runs immediately after configuration loading to prevent the platform from starting in a broken or unsafe state:

1. **Profile Check**: If `APP_ENV` is not one of the 5 explicit profiles, the boot sequence halts with a `ValueError`.
2. **Path Verification**: If `features.historian` is True, the system verifies that the target directory (e.g. `data/`) exists and is writable. If not, it attempts to create it; if it fails, it halts.
3. **Hardware vs Simulation Conflicts**: 
   - If `APP_ENV` is `production` but `features.simulation_engine` is explicitly enabled, the system halts to prevent simulated data from entering the live historian.
   - If `APP_ENV` is `simulation` but a live hardware driver (`modbus_driver`) is enabled, the system halts.
