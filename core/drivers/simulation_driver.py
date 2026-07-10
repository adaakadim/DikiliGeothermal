import logging
from typing import Any, List, Callable
from core.drivers.base_driver import BaseDriver, DriverMetadata, DriverDiagnostics

logger = logging.getLogger(__name__)

class SimulationDriver(BaseDriver):
    """
    Simulation Driver acting as the gateway to the physics-based Digital Twin.
    """
    def __init__(self):
        self._connected = False
        self._diagnostics = DriverDiagnostics(is_connected=False)
        
    def connect(self) -> bool:
        logger.info("Simulation Driver connecting to Digital Twin (STUB)")
        self._connected = True
        self._diagnostics.is_connected = True
        return True
        
    def disconnect(self) -> None:
        logger.info("Simulation Driver disconnecting (STUB)")
        self._connected = False
        self._diagnostics.is_connected = False
        
    def read_tag(self, tag_id: str) -> Any:
        self._diagnostics.read_count += 1
        return 0.0 # STUB
        
    def write_tag(self, tag_id: str, value: Any) -> bool:
        self._diagnostics.write_count += 1
        return True # STUB
        
    def subscribe(self, tag_ids: List[str], callback: Callable[[str, Any], None]) -> bool:
        return True # STUB
        
    def unsubscribe(self, tag_ids: List[str]) -> bool:
        return True # STUB
        
    def browse(self) -> List[str]:
        return [] # STUB
        
    def get_status(self) -> str:
        return "ONLINE" if self._connected else "OFFLINE"
        
    def get_metadata(self) -> DriverMetadata:
        return DriverMetadata(
            name="Digital_Twin_Sim_Core",
            protocol="Internal Physics",
            vendor="DikiliGeothermal",
            version="1.0.0-stub"
        )
        
    def get_diagnostics(self) -> DriverDiagnostics:
        return self._diagnostics
