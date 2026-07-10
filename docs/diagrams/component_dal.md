# Driver Abstraction Layer (DAL) Component Diagram

Shows how the DriverManager abstracts multiple physical protocols.

```mermaid
graph TD
    classDef abstract fill:#9b59b6,stroke:#333,stroke-width:2px,color:#fff
    classDef concrete fill:#e67e22,stroke:#333,stroke-width:2px,color:#fff
    classDef api fill:#ecf0f1,stroke:#333,stroke-width:2px,color:#000

    App[SCADA Engine / AI / Historian]:::api

    subgraph Driver Abstraction Layer
        Manager[DriverManager]:::abstract
        Base[BaseDriver Interface]:::abstract
        
        Manager -- Routes to Active --> Base
        Manager -- Health Checks --> Watchdog
    end

    subgraph Protocol Frameworks
        OPC[OpcUaDriver]:::concrete
        MOD[ModbusDriver]:::concrete
        MQTT[MqttDriver]:::concrete
        SIM[SimulationDriver]:::concrete
        
        Base <|-- OPC
        Base <|-- MOD
        Base <|-- MQTT
        Base <|-- SIM
    end

    App -- read_tag() / write_tag() --> Manager
    App -- subscribe() --> Manager
```
