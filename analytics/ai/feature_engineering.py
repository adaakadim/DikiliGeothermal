"""
analytics/ai/feature_engineering.py
===================================
Automatically calculates derived machine learning features from the raw plant
dataset. These features provide powerful signals for algorithms like Random Forest,
Isolation Forest, and XGBoost.
"""

from typing import List, Dict, Any
import math

class FeatureEngineer:
    """
    Applies feature engineering to raw plant snapshots.
    """
    def __init__(self, window_size: int = 5):
        self.window_size = window_size
        self._flow_history: Dict[str, List[float]] = {}
        
    def process_dataset(self, dataset: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Processes an entire dataset sequentially to maintain rolling windows."""
        processed = []
        for row in dataset:
            processed.append(self.process_row(row))
        return processed

    def process_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates derived features for a single row."""
        new_row = row.copy()
        
        # 1. Temperature & Pressure Differences
        hx_in = row.get("Heat Exchanger Inlet Temperature", 0)
        hx_out = row.get("Heat Exchanger Outlet Temperature", 0)
        new_row["Feature_HX_Temp_Diff"] = round(hx_in - hx_out, 2)
        
        # 2. Thermal Efficiency
        thermal_mw = row.get("Thermal Power (MW)", 0)
        flow_m3h = row.get("Flow Rate (m3/h)", 0)
        if flow_m3h > 0:
            new_row["Feature_Thermal_Efficiency"] = round(thermal_mw / flow_m3h, 4)
        else:
            new_row["Feature_Thermal_Efficiency"] = 0.0
            
        # 3. Pump Load Index
        motor_kw = row.get("Motor Power (kW)", 0)
        # Assume a max motor power of 150 kW for the index
        new_row["Feature_Pump_Load_Index"] = round(motor_kw / 150.0, 3)
        
        # 4. Energy Efficiency Index (MW produced per kW consumed)
        if motor_kw > 0:
            new_row["Feature_Energy_Efficiency_Index"] = round(thermal_mw * 1000 / motor_kw, 2)
        else:
            new_row["Feature_Energy_Efficiency_Index"] = 0.0
            
        # 5. Operating Time Index (normalized hours)
        op_hours = row.get("Pump Operating Hours", 0)
        new_row["Feature_Operating_Time_Index"] = round(op_hours / 10000.0, 3)
        
        # 6. Flow Stability Index (Rolling Standard Deviation)
        wid = row.get("Well ID", "UNKNOWN")
        if wid not in self._flow_history:
            self._flow_history[wid] = []
            
        history = self._flow_history[wid]
        history.append(flow_m3h)
        if len(history) > self.window_size:
            history.pop(0)
            
        if len(history) > 1:
            mean_flow = sum(history) / len(history)
            variance = sum((x - mean_flow) ** 2 for x in history) / (len(history) - 1)
            std_dev = math.sqrt(variance)
            new_row["Feature_Flow_Stability_Index"] = round(std_dev, 2)
        else:
            new_row["Feature_Flow_Stability_Index"] = 0.0

        return new_row
