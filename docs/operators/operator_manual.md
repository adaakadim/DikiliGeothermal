# Operator Manual

Welcome to the DikiliGeothermal SCADA Platform. This manual explains how to navigate the user interface, monitor plant health, and respond to basic events.

## 1. System Login
1. Open the SCADA Client application on your operator workstation.
2. Enter your assigned `Username` and `Password`.
3. Press **Enter**. If you do not have sufficient permissions to view a specific plant area, those tabs will be grayed out.

## 2. Executive Dashboard Navigation
The Executive Dashboard is your primary view.
- **Top Bar**: Displays global plant status, total active alarms, and the current active user.
- **Left Navigation Pane**: Allows switching between Plant Areas (e.g., *Wellheads*, *Pumps*, *Heat Exchangers*).
- **Center Canvas**: Displays real-time telemetry (temperatures, pressures, flow rates) using ISA-101 compliant geometric shapes.

## 3. Digital Twin Interaction
> [!NOTE]
> **[SIMULATION ONLY]** The Digital Twin currently runs in isolation from the physical plant.

To test 'What-If' scenarios:
1. Navigate to the **Digital Twin** tab.
2. Select a simulated equipment piece (e.g., `Sim_W01.Valve`).
3. Enter a new setpoint value (e.g., `45.0` % open).
4. Watch the simulated pressure drop curve update in real-time.

## 4. Alarm Management
The Alarm Banner is permanently docked at the bottom of your screen.
- **Flashing Red / Yellow**: An unacknowledged alarm requires your attention.
- **Click the Alarm**: This opens the Alarm Details window.
- **Acknowledge**: Click the "ACK" button to confirm you have seen the alarm (it will stop flashing).

## 5. Historian Trending
To view past data:
1. Navigate to the **Historian / Trends** tab.
2. Select up to 4 tags from the left-hand tag browser.
3. Select a time range (e.g., *Last 8 Hours*).
4. Click **Plot** to render the line graph.

## 6. AI Prediction Panels
In the right-hand sidebar, the **AI Insights** panel displays anomaly confidence scores.
If a score turns **Red (>85%)**, the AI predicts an impending failure. You should schedule preventative maintenance before the system triggers a hard ISA-18.2 alarm.
