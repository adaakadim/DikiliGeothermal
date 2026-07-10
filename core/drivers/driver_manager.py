import time
import logging
from typing import Dict, Any, List, Optional
from core.drivers.base_driver import BaseDriver, DriverMetadata, DriverDiagnostics
from core.configuration import config

logger = logging.getLogger(__name__)

class DriverManager:
    """
    Centralized driver abstraction layer.
    Routes read/write requests to the currently active driver.
    Registers with the ServiceOrchestrator for health monitoring.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DriverManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self):
        if self._initialized:
            return
            
        self._drivers: Dict[str, BaseDriver] = {}
        self._active_driver_name: Optional[str] = None
        self._active_driver: Optional[BaseDriver] = None
        
        self.total_reads = 0
        self.total_writes = 0
        self.routing_errors = 0
        self._initialized = True

    def register_driver(self, name: str, driver_instance: BaseDriver):
        """Register a driver implementation."""
        if name in self._drivers:
            logger.warning(f"Driver '{name}' is already registered. Overwriting.")
        self._drivers[name] = driver_instance
        logger.info(f"Registered driver: {name}")

    def set_active_driver(self, name: str) -> bool:
        """Switch the active driver routing endpoint."""
        if name not in self._drivers:
            logger.error(f"Cannot set active driver to '{name}'. Driver not registered.")
            return False
            
        if self._active_driver is not None:
            logger.info(f"Disconnecting current driver: {self._active_driver_name}")
            try:
                self._active_driver.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting driver '{self._active_driver_name}': {e}")
                
        self._active_driver_name = name
        self._active_driver = self._drivers[name]
        logger.info(f"Active driver switched to: {name}")
        
        # Automatically connect
        try:
            return self._active_driver.connect()
        except Exception as e:
            logger.critical(f"Failed to connect active driver '{name}': {e}")
            return False

    def health_check(self) -> Dict[str, Any]:
        """Callback for ServiceOrchestrator."""
        health = {
            "status": "ONLINE" if self._active_driver else "WARNING",
            "active_driver": self._active_driver_name,
            "reads": self.total_reads,
            "writes": self.total_writes,
            "routing_errors": self.routing_errors
        }
        
        if self._active_driver:
            try:
                diag = self._active_driver.get_diagnostics()
                health["driver_connected"] = diag.is_connected
                health["driver_latency_ms"] = diag.last_latency_ms
                health["driver_errors"] = diag.error_count
                if not diag.is_connected:
                    health["status"] = "CRITICAL"
            except Exception as e:
                health["status"] = "CRITICAL"
                health["error"] = str(e)
                
        return health

    # ─── DAL Routing Methods ──────────────────────────────────────────────────
    
    def read_tag(self, tag_id: str) -> Any:
        if not self._active_driver:
            self.routing_errors += 1
            raise RuntimeError("No active driver configured.")
        self.total_reads += 1
        return self._active_driver.read_tag(tag_id)
        
    def write_tag(self, tag_id: str, value: Any) -> bool:
        if not self._active_driver:
            self.routing_errors += 1
            raise RuntimeError("No active driver configured.")
        self.total_writes += 1
        return self._active_driver.write_tag(tag_id, value)
        
    def get_metadata(self) -> Optional[DriverMetadata]:
        if not self._active_driver:
            return None
        return self._active_driver.get_metadata()
