# Safety Notes & Operational Boundaries

The DikiliGeothermal SCADA system is a powerful tool capable of manipulating high-pressure, high-temperature industrial environments. Strict adherence to safety boundaries is mandatory.

## 1. Simulation Limitations
> [!WARNING]
> **[SIMULATION ONLY]** Tags
> Any feature, button, or graph tagged with `[SIMULATION ONLY]` in the documentation or UI is currently routed to the local thermodynamic math model. Pressing these buttons will NOT affect physical plant equipment. 
> 
> However, operators MUST treat simulated elements with the exact same gravity as physical equipment to prevent training scars.

## 2. Engineering Approval Required
The following actions cannot be performed by control room operators and require an Engineer with `ADMIN` privileges:
- Changing ISA-18.2 Alarm Thresholds (e.g., raising the High-Pressure alarm limit).
- Bypassing or disabling an active physical Driver.
- Changing the `APP_ENV` deployment profile.

## 3. Real Plant Integration Deferrals
Until the final physical integration phases are complete, the following features are actively disabled in the production profile:
- **Autonomous AI Control**: The AI is strictly read-only. It cannot close valves or turn off pumps.
- **Remote Modbus Writes**: All Modbus registers are mapped as Input Registers (Read-Only) to prevent accidental hardware damage during the testing phase.

## 4. Emergency Procedures
If the HMI provides conflicting information compared to the local gauges on the plant floor, **always trust the physical local gauges**. Initiate a manual Emergency Shutdown (ESD) from the physical plant floor panel if the SCADA system exhibits erratic behavior.
