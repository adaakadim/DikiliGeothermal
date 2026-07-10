import logging
import json
from analytics.ai.random_forest.predictor import predict_plant_state

# Set up logging so we can see the output
logging.basicConfig(level=logging.INFO)

# 1. Create some fake live sensor data
# (This matches the columns the AI expects)
live_data = {
    "Temperature (°C)": 96.5,
    "Pressure (bar)": 5.2,
    "Flow Rate (m3/h)": 118.0,
    "Pump Speed (%)": 100.0,
    "Pump Running (0/1)": 1,
    "Motor Current (A)": 55.2,
    "Motor Voltage (V)": 401.5,
    "Motor Power (kW)": 32.5,
    "Pump Operating Hours": 2500.5,
    "Heat Exchanger Inlet Temperature": 95.0,
    "Heat Exchanger Outlet Temperature": 75.0,
    "Heat Exchanger Efficiency": 90.0,
    "District Heating Supply Temperature": 90.0,
    "District Heating Return Temperature": 50.0,
    "Thermal Power (MW)": 2.5,
    "Pressure Drop": 0.5,
    "Daily Energy": 60.0,
    "Outside Air Temperature": 15.0,
    "Plant Load": 70.0,
    "Alarm Count": 0,
    "Health Score": 95.0,
    
    # Feature Engineering columns
    "Feature_HX_Temp_Diff": 20.0,
    "Feature_Thermal_Efficiency": 0.021,
    "Feature_Pump_Load_Index": 0.21,
    "Feature_Energy_Efficiency_Index": 76.9,
    "Feature_Operating_Time_Index": 0.25,
    "Feature_Flow_Stability_Index": 1.5
}

print("==============================================")
print(" LIVE SENSOR DATA FEED:")
print("==============================================")
for k, v in live_data.items():
    print(f"  {k}: {v}")

print("\n==============================================")
print(" ASKING AI FOR PREDICTION...")
print("==============================================")

# 2. Ask the AI for a prediction!
result = predict_plant_state(live_data)

# Print the result nicely formatted
print(json.dumps(result, indent=4))
print("==============================================")
