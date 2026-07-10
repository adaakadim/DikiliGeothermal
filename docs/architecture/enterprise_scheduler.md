# Enterprise Scheduler

## Purpose
Manages deferred tasks, background workflows, and cron-like recurring jobs without blocking the main event loops.

## Scope
Schedules AI training sequences, historian bulk flushes, and periodic maintenance reports.

## Inputs & Outputs
- **Inputs:** Function callbacks, cron-syntax timing definitions.
- **Outputs:** Asynchronous execution of registered tasks.

## Dependencies
- `core/scheduler/scheduler.py`
- Standard Python `threading` and `time` modules.

## Usage Example
```python
scheduler.schedule_recurring("AI_Training", "0 0 * * *", ai_engine.train)
```

## Future Extensions
Integration with Celery and Redis for distributed task scheduling across a horizontal computing cluster.
