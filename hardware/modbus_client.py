"""
hardware/modbus_client.py
Modbus TCP/RTU client wrapper for field device communication.
Supports both simulation stub and real pymodbus backend.
"""

import logging
import struct
from typing import Optional, Union

logger = logging.getLogger(__name__)

try:
    from pymodbus.client import ModbusTcpClient as _ModbusTcpClient
    from pymodbus.exceptions import ModbusException
    _HAS_PYMODBUS = True
except ImportError:
    _HAS_PYMODBUS = False
    logger.info("pymodbus not installed — ModbusClient running in stub mode.")


class ModbusClient:
    """
    Modbus TCP client with automatic stub fallback when pymodbus is absent.

    Field device addressing (Dikili plant):
      - PLCs at 192.168.10.10 (Well area PLC)
      - PLCs at 192.168.10.20 (HX / Distribution PLC)
    """

    def __init__(self, host: str = "192.168.10.10", port: int = 502,
                 unit_id: int = 1, timeout: float = 3.0):
        self.host    = host
        self.port    = port
        self.unit_id = unit_id
        self.timeout = timeout
        self._client = None
        self._stub_registers: dict[int, int] = {}

    def connect(self) -> bool:
        if _HAS_PYMODBUS:
            self._client = _ModbusTcpClient(self.host, port=self.port, timeout=self.timeout)
            result = self._client.connect()
            logger.info("Modbus %s:%d — %s", self.host, self.port, "connected" if result else "FAILED")
            return result
        else:
            logger.info("Modbus STUB connected to %s:%d", self.host, self.port)
            return True

    def disconnect(self):
        if self._client:
            self._client.close()
        logger.info("Modbus disconnected.")

    def read_holding_register(self, address: int, scale: float = 1.0) -> Optional[float]:
        """Read a 16-bit holding register and apply scaling."""
        if _HAS_PYMODBUS and self._client:
            try:
                rr = self._client.read_holding_registers(address, count=1, slave=self.unit_id)
                if not rr.isError():
                    return rr.registers[0] * scale
            except Exception as exc:
                logger.error("Modbus read error @%d: %s", address, exc)
            return None
        else:
            # Stub: return synthetic value
            return self._stub_registers.get(address, 0) * scale

    def read_float32(self, address: int) -> Optional[float]:
        """Read two consecutive 16-bit registers as IEEE 754 float32."""
        if _HAS_PYMODBUS and self._client:
            try:
                rr = self._client.read_holding_registers(address, count=2, slave=self.unit_id)
                if not rr.isError():
                    raw = struct.pack(">HH", rr.registers[0], rr.registers[1])
                    return struct.unpack(">f", raw)[0]
            except Exception as exc:
                logger.error("Modbus float32 read error @%d: %s", address, exc)
            return None
        return float(self._stub_registers.get(address, 0))

    def write_register(self, address: int, value: Union[int, float], scale: float = 1.0) -> bool:
        """Write a 16-bit holding register."""
        raw = int(value / scale)
        if _HAS_PYMODBUS and self._client:
            try:
                result = self._client.write_register(address, raw, slave=self.unit_id)
                return not result.isError()
            except Exception as exc:
                logger.error("Modbus write error @%d: %s", address, exc)
            return False
        else:
            self._stub_registers[address] = raw
            return True

    @property
    def is_connected(self) -> bool:
        if _HAS_PYMODBUS and self._client:
            return self._client.is_socket_open()
        return True  # stub always "connected"
