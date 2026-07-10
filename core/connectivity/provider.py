"""
core/connectivity/provider.py
=============================
Defines the core IDataProvider interface for data acquisition.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from simulation.sensors import SensorReading

class IDataProvider(ABC):
    """
    Interface for data providers. Abstraction layer to allow swapping
    the data source between Simulator, OPC UA, Modbus TCP, MQTT, REST, etc.
    """

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to the data source."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to the data source."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Return the current connection status."""
        pass

    @abstractmethod
    def read_all(self) -> List[SensorReading]:
        """
        Read all configured sensors/tags.
        Returns a list of SensorReading objects representing the current state.
        """
        pass

    @abstractmethod
    def write_tag(self, tag_id: str, value: Any) -> bool:
        """
        Write a value back to a specific tag (e.g., setpoint control).
        """
        pass
