"""
core/connectivity/mqtt_provider.py
==================================
Stub for future MQTT connectivity.
"""

from typing import List, Any
import logging
from .provider import IDataProvider
from simulation.sensors import SensorReading

logger = logging.getLogger(__name__)

class MQTTDataProvider(IDataProvider):
    """
    Connects to an MQTT Broker to receive telemetry.
    (Future Implementation)
    """

    def __init__(self, broker_url: str, topic: str):
        self.broker_url = broker_url
        self.topic = topic
        self._connected = False

    def connect(self) -> bool:
        logger.info(f"Connecting to MQTT Broker at {self.broker_url} (STUB)")
        self._connected = True
        return True

    def disconnect(self) -> None:
        logger.info("Disconnecting from MQTT Broker (STUB)")
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def read_all(self) -> List[SensorReading]:
        return []

    def write_tag(self, tag_id: str, value: Any) -> bool:
        logger.info(f"MQTT Publish: {tag_id} = {value} (STUB)")
        return True
