# Operator Troubleshooting Guide

This guide assists control room operators in diagnosing and resolving common SCADA issues without requiring immediate IT escalation.

## 1. Dashboard Not Updating / UI Frozen
**Symptoms**: Values on the screen remain static for more than 5 seconds. Clocks may have stopped.
**Likely Causes**: The local browser/HMI client has lost WebSocket connection to the SCADA Core.
**Recovery Steps**:
1. Press `F5` or click the "Refresh Connection" button in the HMI.
2. If the issue persists across multiple workstations, the SCADA Core Engine may be offline. Contact IT immediately.

## 2. Communication Loss (PLC / Hardware Offline)
**Symptoms**: A specific equipment block (e.g., Well 2) turns MAGENTA (Invalid State). A `CRITICAL` alarm fires indicating "Driver Offline".
**Likely Causes**: A network switch failure on the plant floor, a severed ethernet cable, or a tripped breaker on the PLC cabinet.
**Recovery Steps**:
1. Check if *all* equipment is offline or just one node.
2. If one node: Dispatch a maintenance tech to the physical cabinet.
3. If all nodes: Escalate to the Network Engineer.

## 3. Historian Trends Are Blank
**Symptoms**: Clicking "Plot" on a trend graph returns an empty grid.
**Likely Causes**: The Historian backend database (e.g., InfluxDB) is unreachable, or the disk is full.
**Recovery Steps**:
1. Check the System Diagnostics panel for disk space warnings.
2. Do NOT attempt to restart the Historian manually. Log a ticket.

## 4. AI Anomaly Predictions Are Missing
**Symptoms**: The right-hand sidebar shows "AI: OFFLINE".
**Likely Causes**: The Enterprise Scheduler failed to launch the batch inference job, or the Python ML worker crashed.
**Recovery Steps**:
1. Plant operation can safely continue; the AI is strictly read-only and advisory.
2. Inform the Shift Supervisor during handover so the Data Science team can be notified.
