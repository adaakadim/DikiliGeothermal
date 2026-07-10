import logging
import threading
import time
import random
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, List, Callable, Dict, Optional
from core.drivers.base_driver import BaseDriver, DriverMetadata, DriverDiagnostics

logger = logging.getLogger(__name__)

class OpcUaSecurityPolicy(Enum):
    NONE = "None"
    BASIC256SHA256 = "Basic256Sha256"
    AES128_SHA256_RSAOAEP = "Aes128_Sha256_RsaOaep"

class OpcUaSecurityMode(Enum):
    NONE = "None"
    SIGN = "Sign"
    SIGN_AND_ENCRYPT = "SignAndEncrypt"

@dataclass
class OpcUaConfig:
    endpoint_url: str = "opc.tcp://localhost:4840"
    namespace_uri: str = "http://dikiligeothermal.com/scada"
    timeout_ms: int = 5000
    retry_interval_ms: int = 2000
    security_policy: OpcUaSecurityPolicy = OpcUaSecurityPolicy.NONE
    security_mode: OpcUaSecurityMode = OpcUaSecurityMode.NONE
    cert_path: Optional[str] = None
    private_key_path: Optional[str] = None
    simulation_mode: bool = True

class OpcUaDriver(BaseDriver):
    """
    Enterprise OPC UA Driver Framework.
    Implements full session, security, and subscription tracking architecture.
    Currently runs in simulation mode (no real socket connections).
    """
    def __init__(self, config: OpcUaConfig):
        self.config = config
        self._connected = False
        self._session_id: Optional[str] = None
        
        # Diagnostics
        self._diagnostics = DriverDiagnostics(is_connected=False)
        self._connection_attempts = 0
        self._dropped_connections = 0
        
        # Thread safety & Subscriptions
        self._lock = threading.RLock()
        self._subscriptions: Dict[str, List[Callable[[str, Any], None]]] = {}
        self._sim_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
    def connect(self) -> bool:
        with self._lock:
            if self._connected:
                return True
                
            self._connection_attempts += 1
            logger.info(f"OPC UA Driver connecting to {self.config.endpoint_url} (Policy: {self.config.security_policy.value})")
            
            # Simulate network delay and connection success
            time.sleep(0.1)
            
            self._connected = True
            self._session_id = f"session-ns2-{random.randint(1000, 9999)}"
            self._diagnostics.is_connected = True
            self._stop_event.clear()
            
            # Start subscription simulator thread
            if not self._sim_thread or not self._sim_thread.is_alive():
                self._sim_thread = threading.Thread(target=self._subscription_loop, daemon=True)
                self._sim_thread.start()
                
            logger.info(f"OPC UA Session established: {self._session_id}")
            return True
        
    def disconnect(self) -> None:
        with self._lock:
            if not self._connected:
                return
                
            logger.info(f"OPC UA Driver disconnecting session {self._session_id}")
            self._stop_event.set()
            self._connected = False
            self._diagnostics.is_connected = False
            self._session_id = None
            
            if self._sim_thread:
                self._sim_thread.join(timeout=1.0)
                self._sim_thread = None
        
    def read_tag(self, tag_id: str) -> Any:
        with self._lock:
            if not self._connected:
                raise ConnectionError("OPC UA Session is not active.")
                
            start_time = time.perf_counter()
            
            # Simulate network latency
            time.sleep(random.uniform(0.005, 0.020))
            
            self._diagnostics.read_count += 1
            self._diagnostics.last_latency_ms = (time.perf_counter() - start_time) * 1000.0
            
            # Return simulated value based on tag format
            if "temp" in tag_id.lower():
                return 85.0 + random.uniform(-2, 2)
            elif "pressure" in tag_id.lower():
                return 10.0 + random.uniform(-0.5, 0.5)
            elif "flow" in tag_id.lower():
                return 150.0 + random.uniform(-5, 5)
            return 0.0
        
    def write_tag(self, tag_id: str, value: Any) -> bool:
        with self._lock:
            if not self._connected:
                raise ConnectionError("OPC UA Session is not active.")
                
            start_time = time.perf_counter()
            time.sleep(random.uniform(0.010, 0.030))
            
            self._diagnostics.write_count += 1
            self._diagnostics.last_latency_ms = (time.perf_counter() - start_time) * 1000.0
            return True
        
    def subscribe(self, tag_ids: List[str], callback: Callable[[str, Any], None]) -> bool:
        with self._lock:
            if not self._connected:
                raise ConnectionError("OPC UA Session is not active.")
                
            for tag in tag_ids:
                if tag not in self._subscriptions:
                    self._subscriptions[tag] = []
                if callback not in self._subscriptions[tag]:
                    self._subscriptions[tag].append(callback)
            
            logger.debug(f"OPC UA Driver registered subscriptions for {len(tag_ids)} tags.")
            return True
        
    def unsubscribe(self, tag_ids: List[str]) -> bool:
        with self._lock:
            for tag in tag_ids:
                if tag in self._subscriptions:
                    self._subscriptions[tag].clear()
            return True
        
    def browse(self) -> List[str]:
        with self._lock:
            if not self._connected:
                raise ConnectionError("OPC UA Session is not active.")
            # Simulate browsing namespace
            time.sleep(0.05)
            return ["ns=2;s=W01.Temperature", "ns=2;s=W01.Pressure", "ns=2;s=W01.Flow"]
        
    def get_status(self) -> str:
        if not self._connected:
            return "OFFLINE"
        if self._diagnostics.error_count > 10:
            return "WARNING"
        return "ONLINE"
        
    def get_metadata(self) -> DriverMetadata:
        return DriverMetadata(
            name="OPC_UA_Enterprise",
            protocol="OPC UA TCP",
            vendor="DikiliGeothermal",
            version="1.1.0-framework"
        )
        
    def get_diagnostics(self) -> DriverDiagnostics:
        with self._lock:
            # We copy to prevent reference mutation issues
            return DriverDiagnostics(
                is_connected=self._diagnostics.is_connected,
                read_count=self._diagnostics.read_count,
                write_count=self._diagnostics.write_count,
                error_count=self._diagnostics.error_count,
                last_latency_ms=self._diagnostics.last_latency_ms
            )

    def _subscription_loop(self):
        """Simulates asynchronous data changes coming from an OPC UA Server."""
        while not self._stop_event.is_set():
            time.sleep(1.0) # Simulate 1Hz publishing interval
            
            with self._lock:
                if not self._connected:
                    continue
                
                # Fire callbacks for all subscribed tags with simulated random walks
                for tag, callbacks in self._subscriptions.items():
                    if not callbacks:
                        continue
                        
                    sim_val = 0.0
                    if "temp" in tag.lower():
                        sim_val = 85.0 + random.uniform(-1, 1)
                    elif "pressure" in tag.lower():
                        sim_val = 10.0 + random.uniform(-0.1, 0.1)
                        
                    for cb in callbacks:
                        try:
                            cb(tag, sim_val)
                        except Exception as e:
                            logger.error(f"OPC UA Subscription callback failed for {tag}: {e}")
                            self._diagnostics.error_count += 1
