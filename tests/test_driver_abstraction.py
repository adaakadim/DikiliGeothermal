import pytest
from core.drivers.driver_manager import DriverManager
from core.drivers.simulation_driver import SimulationDriver
from core.drivers.opcua_driver import OpcUaDriver, OpcUaConfig
from core.drivers.base_driver import DriverMetadata

def test_driver_registration():
    manager = DriverManager()
    manager._drivers.clear()
    
    sim_driver = SimulationDriver()
    manager.register_driver("simulation", sim_driver)
    
    assert "simulation" in manager._drivers

def test_driver_switching():
    manager = DriverManager()
    manager._drivers.clear()
    
    sim_driver = SimulationDriver()
    opc_config = OpcUaConfig(endpoint_url="opc.tcp://localhost:4840")
    opc_driver = OpcUaDriver(opc_config)
    
    manager.register_driver("simulation", sim_driver)
    manager.register_driver("opcua", opc_driver)
    
    # Test setting active
    assert manager.set_active_driver("simulation") is True
    assert manager._active_driver_name == "simulation"
    assert manager._active_driver.get_diagnostics().is_connected is True
    
    # Test hot swap
    assert manager.set_active_driver("opcua") is True
    assert manager._active_driver_name == "opcua"
    
    # Verify old driver disconnected
    assert sim_driver.get_diagnostics().is_connected is False
    # Verify new driver connected
    assert opc_driver.get_diagnostics().is_connected is True

def test_driver_routing_and_diagnostics():
    manager = DriverManager()
    manager._drivers.clear()
    
    sim_driver = SimulationDriver()
    manager.register_driver("simulation", sim_driver)
    manager.set_active_driver("simulation")
    
    # Route read/write
    manager.read_tag("test_tag")
    manager.write_tag("test_tag", 1.0)
    
    # Check diagnostics from driver
    diag = sim_driver.get_diagnostics()
    assert diag.read_count == 1
    assert diag.write_count == 1
    
    # Check health monitor aggregation
    health = manager.health_check()
    assert health["status"] == "ONLINE"
    assert health["reads"] == 1
    assert health["writes"] == 1

def test_driver_unconfigured_routing():
    manager = DriverManager()
    manager._drivers.clear()
    manager._active_driver = None
    manager._active_driver_name = None
    
    with pytest.raises(RuntimeError):
        manager.read_tag("test_tag")
        
    health = manager.health_check()
    assert health["status"] == "WARNING"
    assert health["routing_errors"] == 1
