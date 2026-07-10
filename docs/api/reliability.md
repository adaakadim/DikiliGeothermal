# Reliability Framework API Reference

## Class: `ServiceOrchestrator`
Location: `core/reliability/service_orchestrator.py`

### `register_service(service_name: str, health_check_func: callable) -> None`
**Purpose**: Enrolls a subsystem into the Watchdog polling loop.
- **Parameters**:
  - `service_name` (str): e.g., `"Historian"`.
  - `health_check_func` (callable): A function returning a boolean.

## Class: `CircuitBreaker`
Location: `core/reliability/circuit_breaker.py`

### `execute(func: callable, *args, **kwargs) -> Any`
**Purpose**: Wraps a potentially dangerous remote call. Trips the breaker if error thresholds are exceeded.
- **Exceptions**: Raises `CircuitOpenException` if the remote service is currently isolated.
