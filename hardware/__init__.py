"""
hardware/__init__.py
Hardware Abstraction Layer — Modbus, OPC-UA, serial drivers
"""
from .modbus_client import ModbusClient
from .opc_ua_client import OPCUAClient
from .io_manager import IOManager

__all__ = ["ModbusClient", "OPCUAClient", "IOManager"]
