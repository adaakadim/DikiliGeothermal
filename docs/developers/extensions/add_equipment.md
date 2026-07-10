# How to Add New Equipment

To add a new pump, valve, or well to the platform:

## 1. Define the Tag Hierarchy
Equipment does not exist as instantiated OOP objects in the core; it exists purely as a logical namespace grouping in the tag dictionary.

Define the new equipment tags (e.g., `W02.Pressure`, `W02.Temperature`).

## 2. Map to the Physical Driver
Update the corresponding hardware mapping:
- For Modbus: Add the registers to the `ModbusRegisterMap` in `SystemConfig`.
- For MQTT: Add the topics to the `MqttTopicMap`.
- For OPC UA: Add the Node IDs.

## 3. Update HMI Layouts
If the operator needs to see the equipment, modify `core/hmi/layout_engine.py` to generate the widgets mapped to your new `W02.*` tags.
