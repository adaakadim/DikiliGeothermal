"""
simulation/__init__.py
Simulation Package — Virtual PLC / sensor emulation
"""
from .plant_simulator import PlantSimulator
from .sensor_emulator import SensorEmulator
from .fault_injector import FaultInjector
from .sensors import GeothermalSensorArray, SensorReading, create_well_array, quick_read

__all__ = [
    "PlantSimulator",
    "SensorEmulator",
    "FaultInjector",
    "GeothermalSensorArray",
    "SensorReading",
    "create_well_array",
    "quick_read",
]
