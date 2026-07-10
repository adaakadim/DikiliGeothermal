# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0-enterprise] - 2026-07-09

### Added
- **Driver Abstraction Layer (DAL)**: Unified `BaseDriver` contract abstracting Modbus, MQTT, and OPC UA.
- **Enterprise Scheduler**: Replaced thread.sleep loops with cron-based background task execution.
- **Circuit Breakers & Watchdog**: Auto-recovery mechanisms for the SCADA Core.
- **AI Anomaly Pipeline**: Integration between Historian arrays and predictive detection thresholds.
- **ISA-18.2 Alarm Framework**: Rigorous state machine for alarm lifecycle management.
- **Deployment Profiles**: Environment-aware configuration via `APP_ENV`.
- **Comprehensive Documentation**: Complete Operator Manual, Developer API guides, and Architectural Mermaid diagrams.

### Changed
- Re-architected all direct PLC calls to route through the `DriverManager`.
- Completely decoupled HMI UI generation from backend business logic.
- Hardened the `Historian` to flush asynchronously using a Parquet-ready buffer to prevent main-thread locking.

### Removed
- Removed hardcoded dummy data loops in favor of the formal Digital Twin physics simulator.
