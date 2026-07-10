import abc
from dataclasses import dataclass
from typing import Any, Dict, List, Callable

@dataclass
class DriverMetadata:
    name: str
    protocol: str
    vendor: str
    version: str

@dataclass
class DriverDiagnostics:
    is_connected: bool
    read_count: int = 0
    write_count: int = 0
    error_count: int = 0
    last_latency_ms: float = 0.0

class BaseDriver(abc.ABC):
    """
    Abstract Base Class for all industrial protocol drivers.
    Enforces a standard contract for connecting and transferring tag data.
    """
    
    @abc.abstractmethod
    def connect(self) -> bool:
        """Establish connection to the device or broker."""
        pass
        
    @abc.abstractmethod
    def disconnect(self) -> None:
        """Close connection."""
        pass
        
    @abc.abstractmethod
    def read_tag(self, tag_id: str) -> Any:
        """Read a single tag synchronously."""
        pass
        
    @abc.abstractmethod
    def write_tag(self, tag_id: str, value: Any) -> bool:
        """Write a single tag synchronously."""
        pass
        
    @abc.abstractmethod
    def subscribe(self, tag_ids: List[str], callback: Callable[[str, Any], None]) -> bool:
        """Subscribe to tag changes."""
        pass
        
    @abc.abstractmethod
    def unsubscribe(self, tag_ids: List[str]) -> bool:
        """Remove subscription for tags."""
        pass
        
    @abc.abstractmethod
    def browse(self) -> List[str]:
        """Browse the address space and return available tags."""
        pass
        
    @abc.abstractmethod
    def get_status(self) -> str:
        """Return high-level status string (e.g. 'CONNECTED', 'FAULT')."""
        pass
        
    @abc.abstractmethod
    def get_metadata(self) -> DriverMetadata:
        """Return driver static metadata."""
        pass
        
    @abc.abstractmethod
    def get_diagnostics(self) -> DriverDiagnostics:
        """Return runtime diagnostics for orchestration monitoring."""
        pass
