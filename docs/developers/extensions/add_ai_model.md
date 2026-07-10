# How to Add a New AI Model

To deploy a new predictive model (e.g., PyTorch vibration analysis):

## 1. Build the Model
Create your Python class inside `core/ai/models/`. It must accept standard arrays (e.g., from Historian queries) and output an anomaly confidence score (0.0 to 1.0).

## 2. Register with the Enterprise Scheduler
Update the `AIEngine` to schedule batch inference through `core/scheduler/scheduler.py`:

```python
def __init__(self, scheduler, historian):
    self.my_new_model = VibrationModel()
    scheduler.schedule_recurring("Vibration_Check", "*/5 * * * *", self._run_inference)

def _run_inference(self):
    data = self.historian.query("W01.Vibration", ...)
    score = self.my_new_model.predict(data)
    if score > 0.85:
        self.alarm_manager.trigger("W01.Vibration.High")
```
