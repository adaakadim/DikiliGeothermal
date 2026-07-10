# How to Add a New Alarm Rule

To add custom trigger conditions (e.g., rate of change alarms, logic-based alarms):

## 1. Locate the Alarm Manager
Alarm conditions are processed in `core/alarms/alarm_manager.py`.

## 2. Define the Rule
Inject a new evaluation block within the `_evaluate_alarms()` method or equivalent rules engine loop.

```python
# Example: Rate of Change Alarm
previous_val = self.historian.get_last_value("W01.Pressure")
current_val = self.engine.read_tag("W01.Pressure")

if (current_val - previous_val) > 10.0:
    self.trigger("W01.Pressure.HighROC", severity="CRITICAL")
```

## 3. Register the Alarm in the UI
Ensure that `core/hmi/alarm_manager_ui.py` is capable of rendering the new `severity` or alarm category correctly using the standard ISA-101 geometric badges.
