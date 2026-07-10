# Reliability Framework

## Purpose
Ensures maximum uptime and fault tolerance across the entire DikiliGeothermal SCADA environment.

## Scope
Provides monitoring (Enterprise Watchdog), failure isolation (Circuit Breakers), and automated recovery sequences (Auto-Recovery Engine). It wraps all critical services but does not execute business logic itself.

## Inputs & Outputs
- **Inputs:** Internal service heartbeats, runtime exceptions, latency metrics.
- **Outputs:** Service restarts, circuit breaker trips (halting failing integrations), and correlated logging output.

## Dependencies
- `core/reliability/watchdog.py`
- `core/reliability/circuit_breaker.py`
- `core/reliability/service_orchestrator.py`

## Usage Example
```python
# Typically instantiated globally via Orchestrator
orchestrator.register_service("Historian", historian.health_check)
```

## Future Extensions
Integration with Kubernetes Liveness/Readiness probes when the SCADA core is containerized and orchestrated via K8s.
