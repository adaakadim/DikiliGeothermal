# Alarm Response Guide

This matrix defines the required operator actions for ISA-18.2 compliant alarms.

## 1. CRITICAL Alarms
**Visual Indication**: Flashing Red Square.
**Audio**: Continuous high-pitched tone.

- **Typical Causes**: Equipment failure, safety limits exceeded (e.g., extreme wellhead pressure), loss of physical PLC communication.
- **Recommended Action**: Immediately isolate the affected subsystem. Switch local control to MANUAL if necessary.
- **Escalation Path**: Contact the Shift Supervisor and Maintenance Engineer immediately.
- **Logging**: The operator MUST enter a text comment into the SCADA system when acknowledging the alarm, detailing the corrective action taken.
- **Acknowledgment**: Must be acknowledged within 60 seconds.

## 2. WARNING Alarms
**Visual Indication**: Flashing Yellow Triangle.
**Audio**: Intermittent chime.

- **Typical Causes**: Variables approaching high/low limits, AI predicting an impending failure, minor sensor drift.
- **Recommended Action**: Monitor the trend in the Historian. Adjust setpoints to bring the process back to center.
- **Escalation Path**: Mention to the next shift during handover. No immediate supervisor escalation required unless it persists.
- **Logging**: Optional.
- **Acknowledgment**: Must be acknowledged within 5 minutes.

## 3. DIAGNOSTIC Alarms
**Visual Indication**: Solid Blue Circle.
**Audio**: Silent.

- **Typical Causes**: Background tasks completed (e.g., Historian flush), user logins, simulation resets.
- **Recommended Action**: No immediate action required.
- **Escalation Path**: None.
- **Logging**: Automatically handled by the `AuditLogger`.
- **Acknowledgment**: Auto-acknowledged by the system.
