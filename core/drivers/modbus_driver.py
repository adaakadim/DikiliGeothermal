import logging
import threading
import time
import random
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, List, Callable, Dict, Optional
from core.drivers.base_driver import BaseDriver, DriverMetadata, DriverDiagnostics

logger = logging.getLogger(__name__)

class ModbusDataType(Enum):
    BOOL = "BOOL"
    INT16 = "INT16"
    UINT16 = "UINT16"
    INT32 = "INT32"
    UINT32 = "UINT32"
    FLOAT32 = "FLOAT32"

class ModbusByteOrder(Enum):
    BIG_ENDIAN = "BIG_ENDIAN"
    LITTLE_ENDIAN = "LITTLE_ENDIAN"

class ModbusRegisterType(Enum):
    COIL = "COIL"
    DISCRETE_INPUT = "DISCRETE_INPUT"
    INPUT_REGISTER = "INPUT_REGISTER"
    HOLDING_REGISTER = "HOLDING_REGISTER"

@dataclass
class ModbusRegisterMap:
    logical_tag: str
    register_type: ModbusRegisterType
    address: int
    data_type: ModbusDataType
    size_words: int = 1
    scale_factor: float = 1.0
    byte_order: ModbusByteOrder = ModbusByteOrder.BIG_ENDIAN

@dataclass
class ModbusConfig:
    host: str = "127.0.0.1"
    port: int = 502
    unit_id: int = 1
    timeout_ms: int = 3000
    retry_interval_ms: int = 2000
    poll_interval_ms: int = 1000
    simulation_mode: bool = True
    register_maps: List[ModbusRegisterMap] = field(default_factory=list)

class ModbusDriver(BaseDriver):
    """
    Enterprise Modbus TCP Driver Framework.
    Implements simulated register mapping, endianness, and background polling.
    """
    def __init__(self, config: ModbusConfig):
        self.config = config
        self._connected = False
        
        # Build map index for fast O(1) lookups
        self._tag_to_map: Dict[str, ModbusRegisterMap] = {
            m.logical_tag: m for m in self.config.register_maps
        }
        
        # Add some default mappings if none provided (for tests/demo)
        if not self._tag_to_map:
            self._tag_to_map["W01.Temperature"] = ModbusRegisterMap(
                "W01.Temperature", ModbusRegisterType.HOLDING_REGISTER, 40001, ModbusDataType.FLOAT32, 2, 0.1
            )
            self._tag_to_map["W01.Pressure"] = ModbusRegisterMap(
                "W01.Pressure", ModbusRegisterType.HOLDING_REGISTER, 40003, ModbusDataType.FLOAT32, 2, 0.1
            )
            self._tag_to_map["W01.PumpRunCommand"] = ModbusRegisterMap(
                "W01.PumpRunCommand", ModbusRegisterType.COIL, 0, ModbusDataType.BOOL
            )
            
        # Diagnostics
        self._diagnostics = DriverDiagnostics(is_connected=False)
        self._connection_attempts = 0
        self._dropped_connections = 0
        self._timeouts = 0
        
        # Thread safety & Polling Subscriptions
        self._lock = threading.RLock()
        self._subscriptions: Dict[str, List[Callable[[str, Any], None]]] = {}
        self._poll_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
    def connect(self) -> bool:
        with self._lock:
            if self._connected:
                return True
                
            self._connection_attempts += 1
            logger.info(f"Modbus TCP Driver connecting to {self.config.host}:{self.config.port} (Unit: {self.config.unit_id})")
            
            # Simulate network delay
            time.sleep(0.05)
            
            self._connected = True
            self._diagnostics.is_connected = True
            self._stop_event.clear()
            
            # Start polling thread
            if not self._poll_thread or not self._poll_thread.is_alive():
                self._poll_thread = threading.Thread(target=self._polling_loop, daemon=True)
                self._poll_thread.start()
                
            logger.info(f"Modbus TCP Socket connected.")
            return True
            
    def disconnect(self) -> None:
        with self._lock:
            if not self._connected:
                return
                
            logger.info(f"Modbus TCP Driver disconnecting from {self.config.host}:{self.config.port}")
            self._stop_event.set()
            self._connected = False
            self._diagnostics.is_connected = False
            
            if self._poll_thread:
                self._poll_thread.join(timeout=2.0)
                self._poll_thread = None
                
    def read_tag(self, tag_id: str) -> Any:
        with self._lock:
            if not self._connected:
                raise ConnectionError("Modbus socket is not active.")
                
            start_time = time.perf_counter()
            
            if tag_id not in self._tag_to_map:
                self._diagnostics.error_count += 1
                raise ValueError(f"Tag {tag_id} not found in Modbus register map.")
                
            reg_map = self._tag_to_map[tag_id]
            
            # Simulate network latency based on register read
            time.sleep(random.uniform(0.010, 0.030))
            
            # Simulated read logic
            val = self._simulate_register_read(reg_map)
            
            self._diagnostics.read_count += 1
            self._diagnostics.last_latency_ms = (time.perf_counter() - start_time) * 1000.0
            
            return val
            
    def write_tag(self, tag_id: str, value: Any) -> bool:
        with self._lock:
            if not self._connected:
                raise ConnectionError("Modbus socket is not active.")
                
            start_time = time.perf_counter()
            
            if tag_id not in self._tag_to_map:
                self._diagnostics.error_count += 1
                raise ValueError(f"Tag {tag_id} not found in Modbus register map.")
                
            reg_map = self._tag_to_map[tag_id]
            
            # Validate write target
            if reg_map.register_type in [ModbusRegisterType.DISCRETE_INPUT, ModbusRegisterType.INPUT_REGISTER]:
                self._diagnostics.error_count += 1
                raise ValueError(f"Cannot write to read-only register type: {reg_map.register_type}")
            
            # Simulate network write latency
            time.sleep(random.uniform(0.015, 0.040))
            
            self._diagnostics.write_count += 1
            self._diagnostics.last_latency_ms = (time.perf_counter() - start_time) * 1000.0
            return True
            
    def subscribe(self, tag_ids: List[str], callback: Callable[[str, Any], None]) -> bool:
        with self._lock:
            if not self._connected:
                raise ConnectionError("Modbus socket is not active.")
                
            for tag in tag_ids:
                if tag not in self._tag_to_map:
                    logger.warning(f"Cannot subscribe to unmapped Modbus tag: {tag}")
                    continue
                    
                if tag not in self._subscriptions:
                    self._subscriptions[tag] = []
                if callback not in self._subscriptions[tag]:
                    self._subscriptions[tag].append(callback)
                    
            logger.debug(f"Modbus Driver registered subscriptions for {len(tag_ids)} tags.")
            return True
            
    def unsubscribe(self, tag_ids: List[str]) -> bool:
        with self._lock:
            for tag in tag_ids:
                if tag in self._subscriptions:
                    self._subscriptions[tag].clear()
            return True
            
    def browse(self) -> List[str]:
        # Modbus doesn't naturally support browse, return local map
        with self._lock:
            return list(self._tag_to_map.keys())
            
    def get_status(self) -> str:
        if not self._connected:
            return "OFFLINE"
        if self._diagnostics.error_count > 10 or self._timeouts > 5:
            return "WARNING"
        return "ONLINE"
        
    def get_metadata(self) -> DriverMetadata:
        return DriverMetadata(
            name="Modbus_TCP_Enterprise",
            protocol="Modbus TCP",
            vendor="DikiliGeothermal",
            version="1.1.0-framework"
        )
        
    def get_diagnostics(self) -> DriverDiagnostics:
        with self._lock:
            return DriverDiagnostics(
                is_connected=self._diagnostics.is_connected,
                read_count=self._diagnostics.read_count,
                write_count=self._diagnostics.write_count,
                error_count=self._diagnostics.error_count,
                last_latency_ms=self._diagnostics.last_latency_ms
            )

    # ─── Internal Simulation Methods ──────────────────────────────────────────
    def _simulate_register_read(self, reg_map: ModbusRegisterMap) -> Any:
        if reg_map.data_type == ModbusDataType.BOOL:
            return random.choice([True, False])
            
        base_val = 0.0
        if "temp" in reg_map.logical_tag.lower():
            base_val = 85.0
        elif "pressure" in reg_map.logical_tag.lower():
            base_val = 10.0
            
        val = base_val + random.uniform(-1, 1)
        # Apply scaling simulation (e.g. PLC sends 850, we scale by 0.1 to get 85.0)
        # Here we just return the scaled float directly for simulation
        return val

    def _polling_loop(self):
        """
        Since Modbus has no subscription mechanism, we poll continuously
        and fire callbacks to simulate an event-driven architecture.
        """
        poll_interval_sec = self.config.poll_interval_ms / 1000.0
        
        while not self._stop_event.is_set():
            time.sleep(poll_interval_sec)
            
            with self._lock:
                if not self._connected:
                    continue
                    
                for tag, callbacks in self._subscriptions.items():
                    if not callbacks:
                        continue
                        
                    try:
                        # Polling the hardware
                        val = self.read_tag(tag)
                        
                        for cb in callbacks:
                            try:
                                cb(tag, val)
                            except Exception as e:
                                logger.error(f"Modbus Subscription callback failed for {tag}: {e}")
                                self._diagnostics.error_count += 1
                    except Exception as e:
                        logger.error(f"Modbus Polling failed for tag {tag}: {e}")
                        self._timeouts += 1
                        self._diagnostics.error_count += 1
