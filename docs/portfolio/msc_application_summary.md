# MSc & Portfolio Application Summary

**Project Name**: DikiliGeothermal SCADA & Digital Twin
**Domain**: Industrial Automation (IIoT), Artificial Intelligence, Software Architecture
**Role**: Lead Architect / Full Stack Engineer

## 1. Executive Summary
DikiliGeothermal is an enterprise-grade Supervisory Control and Data Acquisition (SCADA) platform engineered to manage the high-pressure, thermodynamic realities of a geothermal power plant. 

The core achievement of this repository is its **absolute architectural decoupling**. Unlike legacy industrial systems where UI logic, networking protocols, and business rules are dangerously intertwined, this platform strictly isolates concerns using a centralized **Driver Abstraction Layer (DAL)** and an event-driven **Service Orchestrator**.

## 2. Key Architectural Decisions
- **Unified Hardware Contract**: Implemented a generic `BaseDriver` ABC. The SCADA Core possesses zero knowledge of physical networks. It interacts purely with logical tags (e.g., `read_tag("W01.Pressure")`), while the DAL transparently routes requests to polling threads (Modbus TCP) or asynchronous event loops (OPC UA, MQTT).
- **Asynchronous Data Pipelines**: Integrated a non-blocking Historian that buffers high-frequency telemetry in-memory and flushes to disk (Parquet) on a background thread. This guarantees that disk I/O latency never stalls the real-time control loop.
- **Circuit Breakers & Fault Isolation**: Deployed an Enterprise Watchdog that continuously polls microservice health. If the AI Engine or Historian crashes, a Circuit Breaker isolates the failing module, allowing the core HMI and PLC communications to survive unharmed.
- **ISA-18.2 & ISA-101 Compliance**: Implemented strict geometric layouts and muted gray interfaces to prevent operator alarm fatigue, paired with a deterministic alarm state machine governing `CRITICAL` escalation paths.

## 3. Real-World Viability
This project goes beyond typical academic prototypes. It includes:
- **X.509 TLS Readiness** for secure MQTT Cloud/Edge computing.
- **Environment Bootstrapping** (`APP_ENV`) ensuring code developed against the Digital Twin simulation is exactly the same code executed against physical Siemens/Modicon PLCs.
- **Zero-Regression CI/CD Setup**: Fully tested via an extensive `pytest` suite ensuring 100% regression validation before physical deployment.

**Conclusion**: The DikiliGeothermal platform serves as a modern blueprint for the future of Industrial IoT, proving that critical infrastructure can be driven by Python and AI while maintaining the relentless reliability demanded by the energy sector.
