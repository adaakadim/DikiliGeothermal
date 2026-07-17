# Dikili Geothermal SCADA Platform
*v1.0.0 Release Candidate*

## Project Overview
The Dikili Geothermal SCADA Platform is an industrial-grade control and monitoring interface for geothermal power plants. It integrates real-time physics simulation, Random Forest-based predictive maintenance, and modern ISA-101 HMI visualizations into a single comprehensive operator workspace.

## Features
- **Real-Time Digital Twin**: 2D thermodynamic modeling synchronized with live plant telemetry.
- **AI Operator Assistant**: Autonomous diagnostic engine identifying faults (like pump cavitation or heat exchanger fouling) in real time.
- **Predictive Maintenance**: Estimates the Remaining Useful Life (RUL) of critical components before catastrophic failure.
- **Enterprise Reporting**: One-click generation of PDF and CSV compliance reports.
- **Scenario Manager**: Run "what-if" scenarios directly against the mathematical simulator.

## System Architecture
Built on a strictly decoupled clean architecture:
- **Presentation**: `tkinter` structured with strict ISA-101 layout grids.
- **Application Logic**: Event engines, AI inference pipelines (`sklearn`), and orchestration layers.
- **Persistence**: High-throughput batched SQLite `DataHistorian`.

## Installation

### Requirements
- Python 3.11+
- Windows OS (Tested on Windows 11)
- 4GB RAM Minimum

### Quick Start
1. Clone the repository.
2. Initialize the virtual environment: `python -m venv venv`
3. Install dependencies: `pip install -r requirements.txt`
4. Launch the platform: `python -m gui.app`

## Documentation
- [INSTALL.md](INSTALL.md)
- [USER_MANUAL.md](USER_MANUAL.md)
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)

## License
Proprietary / Closed Source. All Rights Reserved.

## Authors
- Advanced Agentic Coding Team
