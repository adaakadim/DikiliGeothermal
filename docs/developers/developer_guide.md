# Developer Guide

Welcome to the DikiliGeothermal SCADA development environment. This guide explains how to configure your local machine for contributing to the platform.

## 1. Project Architecture Overview
DikiliGeothermal is a multi-layered Python platform. It is strictly decoupled:
- **Presentation**: `core/hmi` (Generates UI layouts).
- **Core Engine**: `core/engine.py` (Maintains state).
- **Driver Abstraction Layer (DAL)**: `core/drivers` (Manages Modbus/OPC UA/MQTT).
- **Intelligence**: `core/historian` and `core/ai` (Data logging and prediction).
- **Reliability**: `core/reliability` (Watchdogs and circuit breakers).

Please refer to the `docs/diagrams/layered_architecture.md` diagram before modifying cross-module interactions.

## 2. Repository Structure
```text
DikiliGeothermal/
├── core/             # Application source code
├── docs/             # Enterprise documentation
├── tests/            # Pytest regression suite
└── CONTRIBUTING.md   # Guidelines for PRs
```

## 3. Dependency Management
We use a standard Python Virtual Environment.
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt  # (Future dependency file)
```

## 4. Build Process
Currently, the platform runs as a pure Python application. Future containerization will utilize `Docker` to bundle the Core Engine and HMI separately.

## 5. Testing Workflow
We use `pytest` for all unit and integration testing.
Run tests via:
```bash
python -m pytest
```

## 6. Release Workflow
1. Code is merged into `develop` via PR.
2. The full test suite runs.
3. A release branch `release/vX.Y.Z` is cut.
4. Final manual HMI simulation testing occurs.
5. Merged into `main` and tagged `vX.Y.Z`.
