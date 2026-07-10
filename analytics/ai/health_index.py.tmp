"""
analytics/ai/health_index.py
============================
Calculates granular health indexes for the geothermal plant components based on
live sensor data, AI failure predictions, and operating physics.
"""

from typing import Dict, Any

class HealthIndexEngine:
    def calculate_indexes(self, live_features: Dict[str, Any], ai_result: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculates health from 0 to 100% for various sub-systems.
        """
        pump_running = live_features.get("Pump Running (0/1)", 1.0) > 0.5
        
        # 1. Pump Health
        failure_prob = ai_result.get("Pump Failure Probability (%)", 0.0)
        flow_rate = live_features.get("Flow Rate (m3/h)", 0.0)
        
        pump_health = 100.0 - failure_prob
        if pump_running and flow_rate < 90.0:
            pump_health -= 15.0  # Flow instability penalty
        pump_health = max(0.0, min(100.0, pump_health))

        # 2. Motor Health
        motor_current = live_features.get("Motor Current (A)", 0.0)
        op_hours = live_features.get("Pump Operating Hours", 0.0)
        
        motor_health = 100.0
        if pump_running:
            if motor_current > 65.0:
                motor_health -= (motor_current - 65.0) * 1.5  # Overcurrent penalty
        
        # Age penalty
        if op_hours > 5000:
            motor_health -= ((op_hours - 5000) / 1000) * 2.0
            
        motor_health = max(0.0, min(100.0, motor_health))

        # 3. Heat Exchanger Health
        hx_eff = live_features.get("Heat Exchanger Efficiency", 100.0)
        hx_health = 100.0
        
        if hx_eff < 85.0:
            hx_health -= (85.0 - hx_eff) * 2.5  # Degradation scaling
            
        hx_health = max(0.0, min(100.0, hx_health))

        # 4. Overall Plant Health
        # Weighted average representing overall system condition
        overall = (pump_health * 0.4) + (motor_health * 0.3) + (hx_health * 0.3)
        
        return {
            "Pump Health": round(pump_health, 1),
            "Motor Health": round(motor_health, 1),
            "Heat Exchanger Health": round(hx_health, 1),
            "Overall Plant Health": round(overall, 1)
        }
