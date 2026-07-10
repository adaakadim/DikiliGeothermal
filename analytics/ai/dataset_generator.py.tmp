"""
analytics/ai/dataset_generator.py
=================================
Generates a realistic historical dataset representing the Dikili Geothermal plant's
operation over time. Simulates normal operations, daily cycles, seasonal variations,
equipment degradation, and probabilistic failure events.

This generator runs independently of the live SCADA engine.
"""

import math
import random
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta

class PlantSimulator:
    """
    Simulates a geothermal plant's historical data snapshot by snapshot.
    """
    def __init__(self, start_date: datetime):
        self.current_time = start_date
        self.step_minutes = 60  # 1 hour per snapshot
        
        self.well_ids = ["GW-01", "GW-02", "GW-03"]
        
        # State tracking per well
        self.pump_operating_hours = {w: random.uniform(1000, 5000) for w in self.well_ids}
        self.pump_health = {w: 100.0 for w in self.well_ids}
        self.pump_running = {w: 1 for w in self.well_ids}
        
        # State tracking for plant
        self.hx_fouling_factor = 0.0
        self.hx_health = 100.0
        
        # Track ongoing failures to allow multi-hour effects
        self.active_failures = {w: None for w in self.well_ids}

    def _get_ambient_temp(self) -> float:
        """Simulate daily and seasonal outside temperature."""
        day_of_year = self.current_time.timetuple().tm_yday
        hour_of_day = self.current_time.hour
        
        # Seasonal base: highest in summer (day 200), lowest in winter (day 15)
        seasonal_base = 15.0 + 10.0 * math.sin((day_of_year - 100) * 2 * math.pi / 365.25)
        
        # Daily variance: highest at 14:00
        daily_var = 5.0 * math.sin((hour_of_day - 8) * 2 * math.pi / 24)
        
        return seasonal_base + daily_var + random.gauss(0, 0.5)

    def _inject_failures(self, well_id: str):
        """Probabilistically trigger and resolve equipment failures."""
        # 1% chance to fix an active failure per hour (simulates maintenance)
        if self.active_failures[well_id] is not None:
            if random.random() < 0.05:
                self.active_failures[well_id] = None
                self.pump_health[well_id] = 100.0
            return

        # Trigger new failures based on degradation
        degradation = 100.0 - self.pump_health[well_id]
        base_prob = 0.001 + (degradation * 0.0005)
        
        if random.random() < base_prob:
            failure_types = ["HIGH_TEMP", "LOW_PRESS", "LOW_FLOW", "PUMP_OVERLOAD", "SENSOR_DRIFT"]
            self.active_failures[well_id] = random.choice(failure_types)

    def generate_snapshot(self) -> List[Dict[str, Any]]:
        """Generates a snapshot of the plant's state for the current hour."""
        rows = []
        ambient_t = self._get_ambient_temp()
        
        # Global plant degradation
        if random.random() < 0.1:
            self.hx_fouling_factor += random.uniform(0, 0.005)
            self.hx_health = max(0.0, 100.0 - (self.hx_fouling_factor * 100))
            
        if self.hx_fouling_factor > 0.8 and random.random() < 0.05:
            # Maintenance cleans the HX
            self.hx_fouling_factor = 0.0
            self.hx_health = 100.0

        for wid in self.well_ids:
            self._inject_failures(wid)
            
            # Base variables
            base_temp = 95.0 + random.gauss(0, 0.5)
            base_pres = 5.0 + random.gauss(0, 0.1)
            base_flow = 120.0 + random.gauss(0, 2.0)
            
            pump_speed = 100.0 if self.pump_running[wid] else 0.0
            
            # Apply failure effects
            failure = self.active_failures[wid]
            if failure == "HIGH_TEMP":
                base_temp += random.uniform(10.0, 15.0)
                self.pump_health[wid] -= 0.5
            elif failure == "LOW_PRESS":
                base_pres -= random.uniform(1.5, 2.5)
                base_flow -= random.uniform(30.0, 50.0)
            elif failure == "LOW_FLOW":
                base_flow -= random.uniform(40.0, 60.0)
                self.pump_health[wid] -= 0.2
            elif failure == "PUMP_OVERLOAD":
                pump_speed = random.uniform(105.0, 120.0)
                base_flow -= random.uniform(10.0, 20.0)
                self.pump_health[wid] -= 1.0
            elif failure == "SENSOR_DRIFT":
                base_temp += random.uniform(-5.0, 5.0)
                base_pres += random.uniform(-1.0, 1.0)
                
            # Ensure boundaries
            base_temp = max(20.0, base_temp)
            base_pres = max(0.0, base_pres)
            base_flow = max(0.0, base_flow)
            
            # Pump degradation over time
            if self.pump_running[wid]:
                self.pump_operating_hours[wid] += (self.step_minutes / 60.0)
                self.pump_health[wid] = max(0.0, self.pump_health[wid] - random.uniform(0.001, 0.005))
            
            # Motor specs based on physics + degradation
            eff_loss = (100.0 - self.pump_health[wid]) / 100.0
            motor_v = 400.0 + random.gauss(0, 2.0)
            motor_i = (base_flow * 0.4) * (1.0 + eff_loss * 0.5) + random.gauss(0, 1.0)
            if pump_speed == 0: motor_i = 0.0
            motor_kw = (motor_v * motor_i * 1.732 * 0.85) / 1000.0
            
            # Heat Exchanger
            hx_in = base_temp
            hx_eff = max(50.0, 95.0 - (self.hx_fouling_factor * 40.0) + random.gauss(0, 0.5))
            hx_out = hx_in - (hx_in * hx_eff / 100.0 * 0.2)
            
            # District Heating
            dh_sup = hx_in - 5.0
            dh_ret = max(40.0, dh_sup - (20.0 + random.gauss(0, 1.0)))
            
            thermal_mw = base_flow * 4.186 * (hx_in - hx_out) / 3600.0
            pressure_drop = base_pres * 0.1 + (self.hx_fouling_factor * 1.5)
            daily_energy = thermal_mw * 24.0
            
            plant_load = max(30.0, 100.0 - (ambient_t * 2))
            
            # Targets
            pump_failure_target = 1 if self.active_failures[wid] else 0
            maint_req = 1 if self.pump_health[wid] < 60.0 or self.hx_health < 60.0 else 0
            hx_fouling_target = 1 if self.hx_fouling_factor > 0.5 else 0
            failure_prob = round(100.0 - self.pump_health[wid], 2)
            rul_days = int(self.pump_health[wid] * 10)
            
            row = {
                "Timestamp": self.current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "Well ID": wid,
                "Temperature (°C)": round(base_temp, 2),
                "Pressure (bar)": round(base_pres, 2),
                "Flow Rate (m3/h)": round(base_flow, 2),
                "Pump Speed (%)": round(pump_speed, 1),
                "Pump Running (0/1)": self.pump_running[wid],
                "Motor Current (A)": round(motor_i, 2),
                "Motor Voltage (V)": round(motor_v, 2),
                "Motor Power (kW)": round(motor_kw, 2),
                "Pump Operating Hours": round(self.pump_operating_hours[wid], 1),
                "Heat Exchanger Inlet Temperature": round(hx_in, 2),
                "Heat Exchanger Outlet Temperature": round(hx_out, 2),
                "Heat Exchanger Efficiency": round(hx_eff, 2),
                "District Heating Supply Temperature": round(dh_sup, 2),
                "District Heating Return Temperature": round(dh_ret, 2),
                "Thermal Power (MW)": round(thermal_mw, 3),
                "Pressure Drop": round(pressure_drop, 2),
                "Daily Energy": round(daily_energy, 2),
                "Outside Air Temperature": round(ambient_t, 2),
                "Plant Load": round(plant_load, 1),
                "Alarm Count": 1 if pump_failure_target else 0,
                "Health Score": round(self.pump_health[wid], 1),
                
                # Targets
                "Target_Pump_Failure": pump_failure_target,
                "Target_Maintenance_Required": maint_req,
                "Target_HX_Fouling": hx_fouling_target,
                "Target_Failure_Probability": failure_prob,
                "Target_Remaining_Useful_Life_Days": rul_days,
                "Target_Equipment_Health": round((self.pump_health[wid] + self.hx_health) / 2.0, 1)
            }
            rows.append(row)
            
        self.current_time += timedelta(minutes=self.step_minutes)
        return rows

def generate_raw_dataset(records_needed: int = 10000) -> List[Dict[str, Any]]:
    """Generates the requested number of raw records."""
    start_time = datetime.now() - timedelta(hours=records_needed // 3)
    simulator = PlantSimulator(start_time)
    
    dataset = []
    while len(dataset) < records_needed:
        dataset.extend(simulator.generate_snapshot())
        
    return dataset[:records_needed]
