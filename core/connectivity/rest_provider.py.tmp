"""
core/connectivity/rest_provider.py
==================================
Stub for future REST API connectivity.
"""

from typing import List, Any
import logging
from .provider import IDataProvider
from simulation.sensors import SensorReading

logger = logging.getLogger(__name__)

class RESTDataProvider(IDataProvider):
    """
    Connects to a REST API to fetch sensor values.
    (Future Implementation)
    """

    def __init__(self, api_url: str):
        self.api_url = api_url
        self._connected = False

    def connect(self) -> bool:
        logger.info(f"Connecting to REST API at {self.api_url} (STUB)")
        self._connected = True
        return True

    def disconnect(self) -> None:
        logger.info("Disconnecting from REST API (STUB)")
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def read_all(self) -> List[SensorReading]:
        return []

    def write_tag(self, tag_id: str, value: Any) -> bool:
        logger.info(f"REST API POST: {tag_id} = {value} (STUB)")
        return True
