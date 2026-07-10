"""
analytics/ai/random_forest/dataset_metadata.py
==============================================
Introspection engine defining the exact Dataset Schema expected 
by the trained Random Forest models. Mocks historical bounds and units.
"""

from typing import Dict, Any, List

class DatasetIntrospector:
    
    @staticmethod
    def get_dataset_overview() -> Dict[str, str]:
        """Returns mock metadata about the original training dataset."""
        return {
            "Dataset Name": "Dikili_Geothermal_Historical_V2",
            "Dataset Version": "2.1.0",
            "Total Samples": "452,000",
            "Number of Features": "27",
            "Number of Target Classes": "2 (Normal, Failure)",
            "Dataset Creation Date": "2026-05-15",
            "Last Training Date": "2026-06-01",
            "Dataset Source": "Dikili Historian DB (PostgreSQL)"
        }
        
    @staticmethod
    def get_feature_schema() -> List[Dict[str, Any]]:
        """Returns the rigorous list of features the model expects."""
        return [
            {"name": "Temperature (°C)", "unit": "°C", "type": "Float", "desc": "Fluid temperature", "min": 20.0, "max": 150.0, "avg": 95.0, "std": 12.5},
            {"name": "Pressure (bar)", "unit": "bar", "type": "Float", "desc": "System pressure", "min": 1.0, "max": 10.0, "avg": 5.5, "std": 1.2},
            {"name": "Flow Rate (m3/h)", "unit": "m3/h", "type": "Float", "desc": "Volumetric flow", "min": 0.0, "max": 300.0, "avg": 120.0, "std": 45.0},
            {"name": "Pump Speed (%)", "unit": "%", "type": "Float", "desc": "VFD speed command", "min": 0.0, "max": 100.0, "avg": 85.0, "std": 20.0},
            {"name": "Pump Running (0/1)", "unit": "Bool", "type": "Integer", "desc": "Pump operational state", "min": 0, "max": 1, "avg": 0.9, "std": 0.3},
            {"name": "Motor Current (A)", "unit": "A", "type": "Float", "desc": "Electrical current draw", "min": 0.0, "max": 150.0, "avg": 55.0, "std": 18.0},
            {"name": "Motor Voltage (V)", "unit": "V", "type": "Float", "desc": "Line voltage", "min": 380.0, "max": 420.0, "avg": 400.0, "std": 5.0},
            {"name": "Motor Power (kW)", "unit": "kW", "type": "Float", "desc": "Active power consumption", "min": 0.0, "max": 90.0, "avg": 35.0, "std": 12.0},
            {"name": "Pump Operating Hours", "unit": "hrs", "type": "Float", "desc": "Cumulative run time", "min": 0.0, "max": 50000.0, "avg": 15000.0, "std": 8000.0},
            {"name": "Heat Exchanger Inlet Temperature", "unit": "°C", "type": "Float", "desc": "HX Primary Inlet", "min": 20.0, "max": 150.0, "avg": 94.0, "std": 12.0},
            {"name": "Heat Exchanger Outlet Temperature", "unit": "°C", "type": "Float", "desc": "HX Primary Outlet", "min": 20.0, "max": 120.0, "avg": 75.0, "std": 10.0},
            {"name": "Heat Exchanger Efficiency", "unit": "%", "type": "Float", "desc": "Calculated thermal exchange", "min": 0.0, "max": 100.0, "avg": 88.0, "std": 5.0},
            {"name": "District Heating Supply Temperature", "unit": "°C", "type": "Float", "desc": "Secondary loop supply", "min": 20.0, "max": 100.0, "avg": 85.0, "std": 8.0},
            {"name": "District Heating Return Temperature", "unit": "°C", "type": "Float", "desc": "Secondary loop return", "min": 20.0, "max": 80.0, "avg": 55.0, "std": 6.0},
            {"name": "Thermal Power (MW)", "unit": "MW", "type": "Float", "desc": "Total energy yield", "min": 0.0, "max": 15.0, "avg": 5.0, "std": 2.0},
            {"name": "Pressure Drop", "unit": "bar", "type": "Float", "desc": "Differential pressure across filter/HX", "min": 0.0, "max": 5.0, "avg": 0.8, "std": 0.4},
            {"name": "Daily Energy", "unit": "MWh", "type": "Float", "desc": "Cumulative daily yield", "min": 0.0, "max": 500.0, "avg": 120.0, "std": 40.0},
            {"name": "Outside Air Temperature", "unit": "°C", "type": "Float", "desc": "Ambient environment", "min": -20.0, "max": 45.0, "avg": 15.0, "std": 10.0},
            {"name": "Plant Load", "unit": "%", "type": "Float", "desc": "Overall facility demand", "min": 0.0, "max": 100.0, "avg": 70.0, "std": 25.0},
            {"name": "Alarm Count", "unit": "Count", "type": "Integer", "desc": "Active warnings", "min": 0, "max": 50, "avg": 2, "std": 3},
            {"name": "Health Score", "unit": "%", "type": "Float", "desc": "Legacy health index", "min": 0.0, "max": 100.0, "avg": 90.0, "std": 15.0},
            {"name": "Feature_HX_Temp_Diff", "unit": "°C", "type": "Float", "desc": "Engineered delta T", "min": 0.0, "max": 50.0, "avg": 19.0, "std": 4.0},
            {"name": "Feature_Thermal_Efficiency", "unit": "Ratio", "type": "Float", "desc": "Engineered metric", "min": 0.0, "max": 1.0, "avg": 0.85, "std": 0.1},
            {"name": "Feature_Pump_Load_Index", "unit": "Ratio", "type": "Float", "desc": "Engineered metric", "min": 0.0, "max": 2.0, "avg": 0.9, "std": 0.2},
            {"name": "Feature_Energy_Efficiency_Index", "unit": "Index", "type": "Float", "desc": "Engineered metric", "min": 0.0, "max": 100.0, "avg": 75.0, "std": 10.0},
            {"name": "Feature_Operating_Time_Index", "unit": "Ratio", "type": "Float", "desc": "Engineered metric", "min": 0.0, "max": 1.0, "avg": 0.5, "std": 0.3},
            {"name": "Feature_Flow_Stability_Index", "unit": "Index", "type": "Float", "desc": "Engineered metric", "min": 0.0, "max": 5.0, "avg": 1.1, "std": 0.5}
        ]
