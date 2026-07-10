"""
hardware/io_manager.py
I/O Manager — abstracts all field I/O reads and writes behind
a unified interface that routes to Modbus, OPC-UA, or simulation.
"""

import logging
from typing import Any, Optional

from .modbus_client import ModbusClient
from .opc_ua_client import OPCUAClient

logger = logging.getLogger(__name__)


# ── Modbus Register Map for Dikili Plant ──────────────────────────────────────
# Format: tag_id → (device, address, scale)
MODBUS_MAP: dict[str, tuple[str, int, float]] = {
    "W-01.TEMP":    ("plc_well", 0x0100, 0.1),
    "W-01.PRES":    ("plc_well", 0x0101, 0.01),
    "W-01.FLOW":    ("plc_well", 0x0102, 0.1),
    "W-01.PUMP_SP": ("plc_well", 0x0110, 0.1),
    "W-02.TEMP":    ("plc_well", 0x0200, 0.1),
    "W-02.PRES":    ("plc_well", 0x0201, 0.01),
    "W-02.FLOW":    ("plc_well", 0x0202, 0.1),
    "W-02.PUMP_SP": ("plc_well", 0x0210, 0.1),
    "W-03.TEMP":    ("plc_well", 0x0300, 0.1),
    "W-03.PRES":    ("plc_well", 0x0301, 0.01),
    "W-03.FLOW":    ("plc_well", 0x0302, 0.1),
    "W-03.PUMP_SP": ("plc_well", 0x0310, 0.1),
    "HX.SUPPLY_TEMP":  ("plc_hx", 0x0100, 0.1),
    "HX.RETURN_TEMP":  ("plc_hx", 0x0101, 0.1),
    "HX.SEC_SUPPLY":   ("plc_hx", 0x0102, 0.1),
    "HX.SEC_RETURN":   ("plc_hx", 0x0103, 0.1),
    "DH.SUPPLY_PRES":  ("plc_hx", 0x0200, 0.01),
    "DH.RETURN_PRES":  ("plc_hx", 0x0201, 0.01),
    "DH.TOTAL_FLOW":   ("plc_hx", 0x0202, 0.1),
}


class IOManager:
    """
    Centralised I/O abstraction layer.

    In simulation mode, all reads return None (values come from PlantSimulator).
    In hardware mode, reads are mapped to physical Modbus registers.
    """

    def __init__(self, config, simulation_mode: bool = True):
        self.config          = config
        self.simulation_mode = simulation_mode

        self._devices: dict[str, ModbusClient] = {}
        self._opc_client: Optional[OPCUAClient] = None

        if not simulation_mode:
            self._init_hardware()

    def _init_hardware(self):
        logger.info("I/O Manager initialising hardware connections...")

        self._devices["plc_well"] = ModbusClient(
            host="192.168.10.10", port=502, unit_id=1
        )
        self._devices["plc_hx"] = ModbusClient(
            host="192.168.10.20", port=502, unit_id=1
        )

        for name, dev in self._devices.items():
            ok = dev.connect()
            logger.info("  Device %-10s: %s", name, "OK" if ok else "FAILED")

        self._opc_client = OPCUAClient()
        self._opc_client.connect()

    def read(self, tag_id: str) -> Optional[Any]:
        if self.simulation_mode:
            return None
        mapping = MODBUS_MAP.get(tag_id)
        if not mapping:
            return None
        device_name, address, scale = mapping
        dev = self._devices.get(device_name)
        return dev.read_holding_register(address, scale) if dev else None

    def write(self, tag_id: str, value: Any) -> bool:
        if self.simulation_mode:
            return True
        mapping = MODBUS_MAP.get(tag_id)
        if not mapping:
            return False
        device_name, address, scale = mapping
        dev = self._devices.get(device_name)
        return dev.write_register(address, value, scale) if dev else False

    def publish_to_historian(self, snapshot: dict) -> int:
        if self._opc_client:
            return self._opc_client.publish_snapshot(snapshot)
        return 0

    def shutdown(self):
        for dev in self._devices.values():
            dev.disconnect()
        if self._opc_client:
            self._opc_client.disconnect()
        logger.info("I/O Manager shut down.")
