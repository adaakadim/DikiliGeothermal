import logging
import threading
import time
import json
import random
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, List, Callable, Dict, Optional
from core.drivers.base_driver import BaseDriver, DriverMetadata, DriverDiagnostics

logger = logging.getLogger(__name__)

class MqttQoS(Enum):
    AT_MOST_ONCE = 0
    AT_LEAST_ONCE = 1
    EXACTLY_ONCE = 2

class MqttPayloadFormat(Enum):
    JSON = "JSON"
    RAW = "RAW"

@dataclass
class MqttTopicMap:
    logical_tag: str
    topic: str
    qos: MqttQoS = MqttQoS.AT_MOST_ONCE
    retain: bool = False
    payload_format: MqttPayloadFormat = MqttPayloadFormat.JSON

@dataclass
class MqttConfig:
    broker_url: str = "mqtt://localhost:1883"
    port: int = 1883
    client_id: str = "scada-enterprise-node"
    username: Optional[str] = None
    password: Optional[str] = None
    tls_enabled: bool = False
    default_qos: MqttQoS = MqttQoS.AT_MOST_ONCE
    timeout_ms: int = 5000
    reconnect_interval_ms: int = 3000
    simulation_mode: bool = True
    topic_maps: List[MqttTopicMap] = field(default_factory=list)

class MqttDriver(BaseDriver):
    """
    Enterprise MQTT Driver Framework.
    Simulates asynchronous publish/subscribe mechanisms matching `paho-mqtt`.
    """
    def __init__(self, config: MqttConfig):
        self.config = config
        self._connected = False
        
        # Build map index for fast lookup
        self._tag_to_map: Dict[str, MqttTopicMap] = {
            m.logical_tag: m for m in self.config.topic_maps
        }
        self._topic_to_map: Dict[str, MqttTopicMap] = {
            m.topic: m for m in self.config.topic_maps
        }
        
        # Default map setup if empty (for tests/demo)
        if not self._tag_to_map:
            default_map1 = MqttTopicMap("W01.Temperature", "telemetry/wells/W01/temperature")
            default_map2 = MqttTopicMap("W01.Pressure", "telemetry/wells/W01/pressure")
            self._tag_to_map["W01.Temperature"] = default_map1
            self._tag_to_map["W01.Pressure"] = default_map2
            self._topic_to_map[default_map1.topic] = default_map1
            self._topic_to_map[default_map2.topic] = default_map2

        # Diagnostics
        self._diagnostics = DriverDiagnostics(is_connected=False)
        self._connection_attempts = 0
        self._reconnect_attempts = 0
        self._published_messages = 0
        self._received_messages = 0
        
        # Thread safety & Callbacks
        self._lock = threading.RLock()
        self._subscriptions: Dict[str, List[Callable[[str, Any], None]]] = {}
        self._sim_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
    def connect(self) -> bool:
        with self._lock:
            if self._connected:
                return True
                
            self._connection_attempts += 1
            protocol = "mqtts" if self.config.tls_enabled else "mqtt"
            logger.info(f"MQTT Driver connecting to {protocol}://{self.config.broker_url}:{self.config.port} as '{self.config.client_id}'")
            
            # Simulate socket latency
            time.sleep(0.05)
            
            self._connected = True
            self._diagnostics.is_connected = True
            self._stop_event.clear()
            
            # Start simulation thread for incoming pub/sub traffic
            if not self._sim_thread or not self._sim_thread.is_alive():
                self._sim_thread = threading.Thread(target=self._simulation_loop, daemon=True)
                self._sim_thread.start()
                
            logger.info("MQTT Broker connected. Session persistence active.")
            return True
            
    def disconnect(self) -> None:
        with self._lock:
            if not self._connected:
                return
                
            logger.info(f"MQTT Driver disconnecting client '{self.config.client_id}'")
            self._stop_event.set()
            self._connected = False
            self._diagnostics.is_connected = False
            
            if self._sim_thread:
                self._sim_thread.join(timeout=1.0)
                self._sim_thread = None
                
    def read_tag(self, tag_id: str) -> Any:
        """
        MQTT is strictly push-based (Pub/Sub). Synchronous reads request the last known retained value.
        In simulation, we return a mock value immediately.
        """
        with self._lock:
            if not self._connected:
                raise ConnectionError("MQTT connection is offline.")
                
            if tag_id not in self._tag_to_map:
                self._diagnostics.error_count += 1
                raise ValueError(f"Tag {tag_id} not mapped to an MQTT Topic.")
                
            start_time = time.perf_counter()
            time.sleep(random.uniform(0.005, 0.015)) # Network jitter
            
            self._diagnostics.read_count += 1
            self._diagnostics.last_latency_ms = (time.perf_counter() - start_time) * 1000.0
            
            # Simulate retained payload
            if "temp" in tag_id.lower():
                return 85.0 + random.uniform(-0.5, 0.5)
            elif "pressure" in tag_id.lower():
                return 10.0 + random.uniform(-0.1, 0.1)
            return 0.0
            
    def write_tag(self, tag_id: str, value: Any) -> bool:
        """Abstracted to a publish command."""
        with self._lock:
            if not self._connected:
                raise ConnectionError("MQTT connection is offline.")
                
            if tag_id not in self._tag_to_map:
                self._diagnostics.error_count += 1
                raise ValueError(f"Tag {tag_id} not mapped to an MQTT Topic.")
                
            topic_map = self._tag_to_map[tag_id]
            start_time = time.perf_counter()
            
            # Simulate publish network latency (QoS 0 is fast, QoS 1/2 is slower)
            latency = 0.01 if topic_map.qos == MqttQoS.AT_MOST_ONCE else 0.03
            time.sleep(latency)
            
            self._published_messages += 1
            self._diagnostics.write_count += 1
            self._diagnostics.last_latency_ms = (time.perf_counter() - start_time) * 1000.0
            return True
            
    def subscribe(self, tag_ids: List[str], callback: Callable[[str, Any], None]) -> bool:
        with self._lock:
            if not self._connected:
                raise ConnectionError("MQTT connection is offline.")
                
            for tag in tag_ids:
                if tag not in self._tag_to_map:
                    logger.warning(f"Cannot subscribe to unmapped MQTT tag: {tag}")
                    continue
                    
                if tag not in self._subscriptions:
                    self._subscriptions[tag] = []
                    # Simulate sending SUBSCRIBE packet to broker
                    topic = self._tag_to_map[tag].topic
                    logger.debug(f"Subscribing to broker topic: {topic}")
                    
                if callback not in self._subscriptions[tag]:
                    self._subscriptions[tag].append(callback)
                    
            logger.debug(f"MQTT Driver registered subscriptions for {len(tag_ids)} logical tags.")
            return True
            
    def unsubscribe(self, tag_ids: List[str]) -> bool:
        with self._lock:
            for tag in tag_ids:
                if tag in self._subscriptions:
                    self._subscriptions[tag].clear()
                    # In real driver, send UNSUBSCRIBE to broker here
            return True
            
    def browse(self) -> List[str]:
        """Returns logical tags mapped to topics."""
        with self._lock:
            return list(self._tag_to_map.keys())
            
    def get_status(self) -> str:
        if not self._connected:
            return "OFFLINE"
        if self._diagnostics.error_count > 10 or self._reconnect_attempts > 5:
            return "WARNING"
        return "ONLINE"
        
    def get_metadata(self) -> DriverMetadata:
        return DriverMetadata(
            name="MQTT_Sparkplug_Enterprise",
            protocol="MQTT",
            vendor="DikiliGeothermal",
            version="1.1.0-framework"
        )
        
    def get_diagnostics(self) -> DriverDiagnostics:
        with self._lock:
            return DriverDiagnostics(
                is_connected=self._diagnostics.is_connected,
                read_count=self._diagnostics.read_count, # Mapped to retained requests
                write_count=self._published_messages,    # Mapped to published messages
                error_count=self._diagnostics.error_count,
                last_latency_ms=self._diagnostics.last_latency_ms
            )

    def _simulation_loop(self):
        """Simulates incoming async PUBLISH messages from edge devices."""
        while not self._stop_event.is_set():
            time.sleep(1.0) # Simulate message arrival frequency
            
            with self._lock:
                if not self._connected:
                    continue
                    
                for tag, callbacks in self._subscriptions.items():
                    if not callbacks:
                        continue
                        
                    topic_map = self._tag_to_map[tag]
                    
                    # Generate mock payload based on format
                    val = 0.0
                    if "temp" in tag.lower():
                        val = 85.0 + random.uniform(-1.0, 1.0)
                    elif "pressure" in tag.lower():
                        val = 10.0 + random.uniform(-0.2, 0.2)
                        
                    # If JSON, we simulate unpacking it
                    if topic_map.payload_format == MqttPayloadFormat.JSON:
                        mock_payload = json.dumps({"value": val, "timestamp": time.time()})
                        try:
                            parsed = json.loads(mock_payload)
                            val = parsed.get("value", 0.0)
                        except json.JSONDecodeError:
                            self._diagnostics.error_count += 1
                            continue
                            
                    self._received_messages += 1
                    
                    for cb in callbacks:
                        try:
                            cb(tag, val)
                        except Exception as e:
                            logger.error(f"MQTT callback failed for logical tag {tag}: {e}")
                            self._diagnostics.error_count += 1
