# Layered Architecture

This diagram illustrates the strict dependency direction within the software stack. Lower layers have absolutely no knowledge of the layers above them.

```mermaid
graph TD
    classDef layer fill:#f9f9f9,stroke:#333,stroke-width:2px,color:#000

    subgraph "1. Presentation Layer (HMI / Dashboards)"
        direction LR
        UI[WorkspaceManager]
        Layout[LayoutEngine]
        AlarmUI[AlarmManagerUI]
    end

    subgraph "2. Application Layer (Coordination)"
        direction LR
        Orchestrator[ServiceOrchestrator]
        Auth[AuthManager]
    end

    subgraph "3. Business Logic (Core Logic)"
        direction LR
        Engine[SCADAEngine]
        Alarms[AlarmManager]
        AI[AIEngine]
        Twin[DigitalTwin]
    end

    subgraph "4. Services (Data Management)"
        direction LR
        Hist[Historian]
        Sched[Scheduler]
        Watchdog[Watchdog]
    end

    subgraph "5. Driver Abstraction Layer (DAL)"
        direction LR
        DrvMgr[DriverManager]
        Base[BaseDriver]
    end

    subgraph "6. Infrastructure (Protocols / Hardware)"
        direction LR
        OPC[OpcUaDriver]
        Modbus[ModbusDriver]
        MQTT[MqttDriver]
    end

    %% Flow of Dependencies
    UI --> Orchestrator
    Layout --> Auth
    
    Orchestrator --> Engine
    Auth --> Engine
    
    Engine --> Hist
    Engine --> Alarms
    AI --> Hist
    Twin --> Hist
    
    Hist --> DrvMgr
    Engine --> DrvMgr
    Alarms --> DrvMgr
    
    DrvMgr --> Base
    Base --> OPC
    Base --> Modbus
    Base --> MQTT

    class "1. Presentation Layer (HMI / Dashboards)" layer
    class "2. Application Layer (Coordination)" layer
    class "3. Business Logic (Core Logic)" layer
    class "4. Services (Data Management)" layer
    class "5. Driver Abstraction Layer (DAL)" layer
    class "6. Infrastructure (Protocols / Hardware)" layer
```
