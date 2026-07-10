"""
core/connectivity/opcua_provider.py
===================================
Stub for future OPC UA connectivity.
"""

from typing import List, Any
import logging
from .provider import IDataProvider
from simulation.sensors import SensorReading

logger = logging.getLogger(__name__)

class OPCUADataProvider(IDataProvider):
    """
    Connects to a physical PLC using the OPC UA protocol.
    (Future Implementation)
    """

    def __init__(self, endpoint_url: str):
        self.endpoint_url = endpoint_url
        self._connected = False

    def connect(self) -> bool:
        logger.info(f"Connecting to OPC UA server at {self.endpoint_url} (STUB)")
        self._connected = True
        return True

    def disconnect(self) -> None:
        logger.info("Disconnecting from OPC UA server (STUB)")
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def read_all(self) -> List[SensorReading]:
        # Return empty list as this is a stub
        return []

    def write_tag(self, tag_id: str, value: Any) -> bool:
        logger.info(f"OPC UA Write: {tag_id} = {value} (STUB)")
        return True
