import pytest
import time
from core.drivers.opcua_driver import OpcUaDriver, OpcUaConfig, OpcUaSecurityPolicy

def test_opcua_driver_lifecycle():
    config = OpcUaConfig(endpoint_url="opc.tcp://test:4840")
    driver = OpcUaDriver(config)
    
    assert driver.get_status() == "OFFLINE"
    
    # Test Connect
    assert driver.connect() is True
    assert driver.get_status() == "ONLINE"
    assert driver._session_id is not None
    assert driver._diagnostics.is_connected is True
    
    # Test Read
    val = driver.read_tag("ns=2;s=W01.Temperature")
    assert isinstance(val, float)
    
    # Check Diagnostics
    diag = driver.get_diagnostics()
    assert diag.read_count == 1
    assert diag.last_latency_ms > 0
    
    # Test Disconnect
    driver.disconnect()
    assert driver.get_status() == "OFFLINE"
    assert driver._session_id is None
    assert driver._diagnostics.is_connected is False

def test_opcua_driver_subscription():
    config = OpcUaConfig(endpoint_url="opc.tcp://test:4840")
    driver = OpcUaDriver(config)
    driver.connect()
    
    callback_fired = False
    received_val = None
    
    def mock_callback(tag: str, value: float):
        nonlocal callback_fired, received_val
        callback_fired = True
        received_val = value
        
    # Subscribe to a tag
    driver.subscribe(["ns=2;s=W01.Pressure"], mock_callback)
    
    # Wait for the simulation loop to fire the callback (1Hz interval)
    time.sleep(1.2)
    
    assert callback_fired is True
    assert received_val is not None
    
    # Unsubscribe
    driver.unsubscribe(["ns=2;s=W01.Pressure"])
    
    driver.disconnect()

def test_opcua_driver_disconnected_exceptions():
    config = OpcUaConfig(endpoint_url="opc.tcp://test:4840")
    driver = OpcUaDriver(config)
    
    with pytest.raises(ConnectionError):
        driver.read_tag("ns=2;s=W01.Temperature")
        
    with pytest.raises(ConnectionError):
        driver.write_tag("ns=2;s=W01.Temperature", 100.0)
        
    with pytest.raises(ConnectionError):
        driver.browse()
