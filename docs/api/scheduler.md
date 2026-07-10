# Enterprise Scheduler API Reference

## Class: `Scheduler`
Location: `core/scheduler/scheduler.py`

### `schedule_recurring(job_id: str, cron_expression: str, func: callable) -> None`
**Purpose**: Registers a background task.
- **Parameters**:
  - `job_id` (str)
  - `cron_expression` (str): Standard Linux cron syntax.
  - `func` (callable): Function to fire.
