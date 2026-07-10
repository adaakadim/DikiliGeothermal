"""
core/connectivity/protocols.py
==============================
Modular protocol interfaces for future industrial communication support.
Defines base abstraction layers that future implementations must fulfill.
"""

from abc import ABC, abstractmethod

class BaseProtocol(ABC):
    @abstractmethod
    def connect(self) -> bool:
        pass
        
    @abstractmethod
    def disconnect(self):
        pass
        
    @abstractmethod
    def read_tag(self, tag_id: str) -> any:
        pass
        
    @abstractmethod
    def write_tag(self, tag_id: str, value: any) -> bool:
        pass


class ModbusTCP(BaseProtocol):
    """Placeholder for future Modbus TCP implementation."""
    pass

class OPCUA(BaseProtocol):
    """Placeholder for future OPC UA implementation."""
    pass

class MQTT(BaseProtocol):
    """Placeholder for future MQTT implementation."""
    pass

class EtherNetIP(BaseProtocol):
    """Placeholder for future EtherNet/IP implementation."""
    pass

class PROFINET(BaseProtocol):
    """Placeholder for future PROFINET implementation."""
    pass
