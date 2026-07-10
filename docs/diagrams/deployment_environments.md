# Deployment Environments Diagram

Illustrates the physical networking layers across the various deployment stages.

```mermaid
graph TD
    classDef env fill:#bdc3c7,stroke:#333,stroke-width:2px,color:#000
    classDef scada fill:#3498db,stroke:#333,stroke-width:2px,color:#fff
    classDef hw fill:#2c3e50,stroke:#333,stroke-width:2px,color:#fff

    subgraph Development (APP_ENV=development)
        direction LR
        DevScada[SCADA Core]:::scada <--> DevTwin[Local Simulation Twin]:::hw
    end

    subgraph Simulation / QA (APP_ENV=simulation)
        direction LR
        SimScada[SCADA Core]:::scada <--> ClusterTwin[Cloud Digital Twin Cluster]:::hw
    end

    subgraph Pilot / Production (APP_ENV=pilot | production)
        direction LR
        ProdScada[SCADA Core]:::scada
        
        subgraph Real-World
            PLC1[Siemens S7-1500]:::hw
            PLC2[Schneider Modicon]:::hw
            Edge[IIoT Edge Gateway]:::hw
        end
        
        ProdScada <-->|OPC UA| PLC1
        ProdScada <-->|Modbus TCP| PLC2
        ProdScada <-->|MQTT (Sparkplug B)| Edge
    end
```
