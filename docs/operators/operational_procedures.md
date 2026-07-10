# Operational Procedures

This document defines the standard operating procedures (SOPs) for the DikiliGeothermal SCADA system.

## 1. System Startup
1. Ensure the underlying database servers (if applicable) are running.
2. Launch the SCADA Core executable.
3. Observe the boot sequence. Ensure the **Driver Abstraction Layer (DAL)** reports a status of `ONLINE` for all configured drivers.
4. Launch the Operator HMI clients.

## 2. Normal Operation
During normal steady-state operation:
- The dashboard backgrounds should remain neutral gray (ISA-101 compliant).
- The Alarm Banner should be empty or contain only acknowledged (steady) low-priority warnings.
- The AI Anomaly scores should hover below 30%.

## 3. Planned Shutdown
> [!CAUTION]
> A planned shutdown of the SCADA Core will cause a temporary loss of visibility to the physical plant.

1. Notify all active operators of the impending shutdown.
2. Acknowledge any critical alarms.
3. Use the **System Administration** tab to execute a graceful shutdown. This ensures the Historian flushes its memory buffers to disk safely.

## 4. Emergency Shutdown [SIMULATION ONLY]
In the event of an emergency (e.g., wellhead blowout):
1. Navigate to the **Safety Systems** tab.
2. Click the large red **ESD (Emergency Shutdown)** button.
3. Confirm the prompt.
4. *Note: Currently, this only shuts down simulated valves in the Digital Twin environment.*

## 5. Recovery After Restart
When recovering from an unexpected power loss or crash:
1. The **Enterprise Watchdog** will automatically attempt to restart the failed SCADA service.
2. Upon UI reconnection, operators must check the **Historian Gap Report** to see if any data was lost during the outage.
3. Verify that all physical PLC drivers have successfully reconnected (`ONLINE` state).
