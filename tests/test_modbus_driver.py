import pytest
import time
from core.drivers.modbus_driver import ModbusDriver, ModbusConfig, ModbusRegisterMap, ModbusRegisterType, ModbusDataType

def test_modbus_driver_lifecycle():
    config = ModbusConfig(host="127.0.0.1", port=502)
    driver = ModbusDriver(config)
    
    assert driver.get_status() == "OFFLINE"
    
    # Test Connect
    assert driver.connect() is True
    assert driver.get_status() == "ONLINE"
    assert driver._diagnostics.is_connected is True
    
    # Test Read
    val = driver.read_tag("W01.Temperature")
    assert isinstance(val, float)
    
    # Check Diagnostics
    diag = driver.get_diagnostics()
    assert diag.read_count == 1
    assert diag.last_latency_ms > 0
    
    # Test Disconnect
    driver.disconnect()
    assert driver.get_status() == "OFFLINE"
    assert driver._diagnostics.is_connected is False

def test_modbus_register_mapping():
    # Setup custom map
    custom_map = ModbusRegisterMap(
        logical_tag="Custom.Tag",
        register_type=ModbusRegisterType.HOLDING_REGISTER,
        address=40100,
        data_type=ModbusDataType.INT16
    )
    config = ModbusConfig(register_maps=[custom_map])
    driver = ModbusDriver(config)
    driver.connect()
    
    # Should be able to read custom tag
    val = driver.read_tag("Custom.Tag")
    assert val is not None
    
    # Should raise error for unknown tag
    with pytest.raises(ValueError):
        driver.read_tag("Unknown.Tag")
        
    driver.disconnect()

def test_modbus_driver_subscription_polling():
    config = ModbusConfig(poll_interval_ms=500)
    driver = ModbusDriver(config)
    driver.connect()
    
    callback_fired = False
    received_val = None
    
    def mock_callback(tag: str, value: float):
        nonlocal callback_fired, received_val
        callback_fired = True
        received_val = value
        
    # Subscribe to a tag
    driver.subscribe(["W01.Pressure"], mock_callback)
    
    # Wait for the simulation polling loop to fire the callback
    time.sleep(1.0)
    
    assert callback_fired is True
    assert received_val is not None
    
    # Unsubscribe
    driver.unsubscribe(["W01.Pressure"])
    driver.disconnect()

def test_modbus_driver_write_readonly_error():
    # Attempting to write to an input register should fail
    custom_map = ModbusRegisterMap(
        logical_tag="Input.Tag",
        register_type=ModbusRegisterType.INPUT_REGISTER,
        address=30001,
        data_type=ModbusDataType.INT16
    )
    config = ModbusConfig(register_maps=[custom_map])
    driver = ModbusDriver(config)
    driver.connect()
    
    with pytest.raises(ValueError, match="read-only"):
        driver.write_tag("Input.Tag", 10)
        
    driver.disconnect()
