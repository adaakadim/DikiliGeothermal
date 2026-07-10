# 5-Minute Quick Demo Guide

This guide allows an evaluator (recruiter, professor, or peer engineer) to instantly launch the DikiliGeothermal SCADA platform locally and experience the core architecture without requiring any physical PLC hardware.

## Prerequisites
- Python 3.13+
- Git

## Step 1: Launch the System in Simulation Mode
The system uses the `APP_ENV` variable to dynamically map physical endpoints to internal Python thermodynamic loops.

```bash
# Set the environment and launch the Core
APP_ENV=simulation python -m core.main
```
*Expected Output*: The terminal will output `[INFO] SimulationDriver ONLINE` and `[INFO] SCADA Engine Listening`.

## Step 2: Trigger a Simulated Alarm
We will manually override the Digital Twin to push a critical pressure wave.
1. Open the HMI interface.
2. Navigate to the **Digital Twin** tab.
3. Locate `Sim_W01.Pressure` and force the setpoint to `120.0` PSI.
4. **Expected Output**: 
   - The UI gauge for Well 1 will instantly spike.
   - The background will turn solid red, and the ISA-18.2 Alarm Banner will flash `CRITICAL: W01 High Pressure`.

## Step 3: Observe the AI Anomaly Detector
1. Leave the pressure slightly elevated (e.g., `85.0` PSI).
2. Wait approximately 60 seconds for the `Enterprise Scheduler` to trigger the AI inference batch.
3. Open the right-hand **AI Insights** panel.
4. **Expected Output**: The anomaly confidence score will climb from `0.0` to `~0.82`, and an advisory warning will state: *"Impending Pressure Threshold Breach Detected."*

## Step 4: Verify the Historian Parquet Flush
1. Terminate the application (`Ctrl+C`).
2. Navigate to the `data/historian/` directory.
3. **Expected Output**: You will see a freshly written file (e.g., `flush_1700000.csv` or `.parquet`). This proves the asynchronous data pipeline successfully persisted the incident without locking the main thread.
