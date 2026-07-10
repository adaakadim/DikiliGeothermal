"""
core/connectivity/modbus_provider.py
====================================
Stub for future Modbus TCP connectivity.
"""

from typing import List, Any
import logging
from .provider import IDataProvider
from simulation.sensors import SensorReading

logger = logging.getLogger(__name__)

class ModbusTCPDataProvider(IDataProvider):
    """
    Connects to a physical PLC using the Modbus TCP protocol.
    (Future Implementation)
    """

    def __init__(self, host: str, port: int = 502):
        self.host = host
        self.port = port
        self._connected = False

    def connect(self) -> bool:
        logger.info(f"Connecting to Modbus TCP at {self.host}:{self.port} (STUB)")
        self._connected = True
        return True

    def disconnect(self) -> None:
        logger.info("Disconnecting from Modbus TCP (STUB)")
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def read_all(self) -> List[SensorReading]:
        return []

    def write_tag(self, tag_id: str, value: Any) -> bool:
        logger.info(f"Modbus TCP Write: {tag_id} = {value} (STUB)")
        return True
