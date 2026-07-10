# DikiliGeothermal SCADA Documentation Index

Welcome to the enterprise documentation for the **DikiliGeothermal AI-Powered Industrial SCADA & Digital Twin Platform**. This index serves as the central hub for developers, operators, and reviewers navigating the platform's architecture.

**Version:** 1.0.0-enterprise
**Last Updated:** Phase 8.7.1

## Table of Contents

### 1. Architecture Reference
Detailed explanations of the major platform subsystems.
- [SCADA Core Engine](architecture/scada_core.md)
- [Digital Twin Simulator](architecture/digital_twin.md)
- [AI Engine](architecture/ai_engine.md)
- [Historian Pipeline](architecture/historian.md)
- [Enterprise Scheduler](architecture/enterprise_scheduler.md)
- [Driver Abstraction Layer (DAL)](architecture/driver_abstraction_layer.md)
- [Reliability Framework](architecture/reliability_framework.md)
- [Security Model](architecture/security.md)
- [Human-Machine Interface (HMI)](architecture/hmi.md)

### 2. Deployment & Operations
Guides for provisioning, configuring, and operating the platform.
- [Configuration Guide](deployment/configuration_guide.md)
- [Deployment Profiles](deployment/deployment_profiles.md)

**Operations Handbook:**
- [Operator Manual](operators/operator_manual.md)
- [Operational Procedures](operators/operational_procedures.md)
- [Alarm Response Guide](operators/alarm_response_guide.md)
- [Daily Checklists](operators/daily_checklists.md)
- [Safety Notes](operators/safety_notes.md)
- [Operator Troubleshooting](troubleshooting/operator_troubleshooting.md)

### 3. Architecture Diagrams
High-level and component-level graphical representations of the system.
- [System Architecture](diagrams/system_architecture.md)
- [Layered Architecture](diagrams/layered_architecture.md)
- [Deployment Environments](diagrams/deployment_environments.md)

**Component Diagrams:**
- [AI Pipeline Component](diagrams/component_ai_pipeline.md)
- [Driver Abstraction Layer (DAL)](diagrams/component_dal.md)
- [Digital Twin Simulator](diagrams/component_digital_twin.md)
- [Reliability Framework](diagrams/component_reliability.md)
- [Security Framework](diagrams/component_security.md)

**Data Flow Diagrams:**
- [Telemetry Pipeline](diagrams/data_flow_telemetry.md)
- [Alarm Lifecycle](diagrams/data_flow_alarms.md)
- [Authentication Flow](diagrams/data_flow_authentication.md)

### 4. Developer Standards
### 5. Developer Guide & Contribution Workflow
Guidelines for configuring local environments and submitting code.
- [Developer Guide](developers/developer_guide.md)
- [Contribution Workflow](../CONTRIBUTING.md)

**Extension Guides (How-To's):**
- [Add a New Driver](developers/extensions/add_driver.md)
- [Add a New AI Model](developers/extensions/add_ai_model.md)
- [Add New Equipment](developers/extensions/add_equipment.md)
- [Add a New Alarm Rule](developers/extensions/add_alarm_rule.md)
- [Add a Historian Backend](developers/extensions/add_historian_backend.md)

### 6. API Reference
Strict interface contracts for major subsystems.
- [SCADA Core Engine API](api/scada_core.md)
- [Driver Abstraction Layer API](api/driver_layer.md)
- [Historian API](api/historian.md)
- [Reliability Framework API](api/reliability.md)
- [AI Engine API](api/ai_engine.md)
- [Scheduler API](api/scheduler.md)
- [Security API](api/security.md)
- [Configuration System API](api/configuration.md)

---
*Note: This platform is designed for academic review and open-source modularity. Please ensure all contributions adhere to the [Documentation Standards](developers/documentation_standards.md).*
