import pytest
import time
from core.drivers.mqtt_driver import MqttDriver, MqttConfig, MqttTopicMap, MqttQoS, MqttPayloadFormat

def test_mqtt_driver_lifecycle():
    config = MqttConfig(broker_url="mqtt://localhost")
    driver = MqttDriver(config)
    
    assert driver.get_status() == "OFFLINE"
    
    # Test Connect
    assert driver.connect() is True
    assert driver.get_status() == "ONLINE"
    assert driver._diagnostics.is_connected is True
    
    # Test Publish / Write
    assert driver.write_tag("W01.Temperature", 90.0) is True
    
    # Check Diagnostics
    diag = driver.get_diagnostics()
    assert diag.write_count == 1
    assert diag.last_latency_ms > 0
    
    # Test Disconnect
    driver.disconnect()
    assert driver.get_status() == "OFFLINE"
    assert driver._diagnostics.is_connected is False

def test_mqtt_topic_mapping():
    # Setup custom map
    custom_map = MqttTopicMap(
        logical_tag="Custom.Tag",
        topic="edge/device1/custom",
        payload_format=MqttPayloadFormat.RAW
    )
    config = MqttConfig(topic_maps=[custom_map])
    driver = MqttDriver(config)
    driver.connect()
    
    # Should be able to write (publish) to custom tag
    assert driver.write_tag("Custom.Tag", 100) is True
    
    # Should raise error for unknown tag
    with pytest.raises(ValueError):
        driver.write_tag("Unknown.Tag", 100)
        
    driver.disconnect()

def test_mqtt_driver_subscription_event_loop():
    config = MqttConfig()
    driver = MqttDriver(config)
    driver.connect()
    
    callback_fired = False
    received_val = None
    
    def mock_callback(tag: str, value: float):
        nonlocal callback_fired, received_val
        callback_fired = True
        received_val = value
        
    # Subscribe to a tag
    driver.subscribe(["W01.Pressure"], mock_callback)
    
    # Wait for the simulation event loop to fire the callback
    time.sleep(1.2)
    
    assert callback_fired is True
    assert received_val is not None
    
    # Unsubscribe
    driver.unsubscribe(["W01.Pressure"])
    driver.disconnect()

def test_mqtt_driver_disconnected_exceptions():
    config = MqttConfig()
    driver = MqttDriver(config)
    
    with pytest.raises(ConnectionError):
        driver.read_tag("W01.Temperature")
        
    with pytest.raises(ConnectionError):
        driver.write_tag("W01.Temperature", 100.0)
