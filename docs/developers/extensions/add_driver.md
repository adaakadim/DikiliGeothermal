# How to Add a New Driver

To integrate a new physical protocol (e.g., DNP3, BACnet) into DikiliGeothermal, you must build a class that strictly implements the `BaseDriver` abstract base class.

## 1. Create the Driver Class
Create a new file `core/drivers/dnp3_driver.py`:

```python
from core.drivers.base_driver import BaseDriver, DriverDiagnostics

class Dnp3Driver(BaseDriver):
    def __init__(self, config):
        super().__init__()
        self.config = config
        
    def connect(self) -> bool:
        # Implement physical connection logic
        return True
        
    def disconnect(self) -> None:
        pass
        
    def read_tag(self, logical_tag: str) -> float:
        # Map logical to physical address
        return 0.0
        
    def write_tag(self, logical_tag: str, value: float) -> bool:
        return True
```

## 2. Implement the Thread-Safe Subscribe Loop
If your protocol is event-driven, implement a daemon thread `_simulation_loop` (similar to MQTT). If polling, implement a background polling thread (similar to Modbus).

## 3. Register with DriverManager
Update `core/drivers/driver_manager.py` to instantiate your driver when the appropriate `DriverConfig` is loaded.
