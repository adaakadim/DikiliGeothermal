"""
analytics/optimization/efficiency_analyzer.py
=============================================
Calculates engineering Key Performance Indicators (KPIs) regarding energy efficiency, 
thermal performance, and power consumption based on live telemetry.
"""

from typing import Dict, Any

class EfficiencyAnalyzer:
    def __init__(self):
        # Nominal reference values for calculation
        self.nominal_pump_power_kw = 250.0  # Assumed nominal for P-101
        self.nominal_hx_capacity_mw = 50.0  # Assumed nominal heat transfer
        self.cp_brine = 4.18 # kJ/kg.K approx
        
    def analyze(self, live_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Analyze live SCADA data to produce efficiency metrics.
        """
        kpis = {}
        
        # 1. Pump P-101 Efficiency Estimate
        p101_current = live_data.get("P-101 Motor Current (A)", 0.0)
        p101_pressure = live_data.get("P-101 Discharge Pressure (bar)", 1.0)
        gw01_flow = live_data.get("GW-01 Flow Rate (t/h)", 0.1)
        
        # Simple hydraulic power estimation: Flow * Pressure * constant
        # Motor power estimation: Current * Voltage (assume 400V) * PF * sqrt(3)
        # We will use a simplified ratio for demonstration
        if p101_current > 10:
            power_kw = (p101_current * 400 * 0.85 * 1.732) / 1000.0
            hydraulic_power = (gw01_flow / 3.6) * (p101_pressure * 100) / 1000.0 # roughly kW
            # Normalize to realistic percentage
            pump_eff = (hydraulic_power / power_kw) * 100 * 2.5 # scaling factor
            kpis["Pump Efficiency (%)"] = min(95.0, max(10.0, pump_eff))
        else:
            kpis["Pump Efficiency (%)"] = 0.0

        # 2. Heat Exchanger (HX-101) Performance
        pri_in = live_data.get("HX-101 Primary Inlet Temp (°C)", 160.0)
        pri_out = live_data.get("HX-101 Primary Outlet Temp (°C)", 80.0)
        sec_in = live_data.get("HX-101 Secondary Inlet Temp (°C)", 60.0)
        sec_out = live_data.get("HX-101 Secondary Outlet Temp (°C)", 110.0)
        
        # Thermal efficiency of HX = Heat absorbed by secondary / Heat given by primary
        # Assuming equal flow rates for simplified demonstration, it's just temp differences
        delta_pri = max(1.0, pri_in - pri_out)
        delta_sec = max(0.0, sec_out - sec_in)
        
        if pri_in > 50:
            # Theoretical max transfer = pri_in - sec_in
            max_transfer = pri_in - sec_in
            hx_eff = (delta_sec / max_transfer) * 100.0 if max_transfer > 0 else 0
            kpis["Heat Exchanger Efficiency (%)"] = min(98.0, max(20.0, hx_eff))
        else:
            kpis["Heat Exchanger Efficiency (%)"] = 0.0
            
        # 3. Overall Plant Efficiency & Thermal Power
        # Thermal Power MW = flow(kg/s) * Cp * (pri_in - pri_out)
        flow_kg_s = gw01_flow * (1000 / 3600)
        thermal_power_mw = (flow_kg_s * self.cp_brine * delta_pri) / 1000.0
        kpis["Thermal Power (MW)"] = thermal_power_mw
        
        # Plant Load %
        kpis["Plant Load (%)"] = min(100.0, (thermal_power_mw / self.nominal_hx_capacity_mw) * 100.0)
        
        # Overall Efficiency (simplified: combination of HX and Pump efficiencies)
        overall_eff = (kpis["Heat Exchanger Efficiency (%)"] * 0.7) + (kpis["Pump Efficiency (%)"] * 0.3)
        kpis["Overall Plant Efficiency (%)"] = min(95.0, max(0.0, overall_eff))
        
        # Energy Utilization Index (EUI)
        if thermal_power_mw > 0:
            total_power_kw = kpis.get("Pump Efficiency (%)", 50) * 5 # mock total power
            kpis["Specific Energy Consumption (kWh/MWh_th)"] = total_power_kw / thermal_power_mw
        else:
            kpis["Specific Energy Consumption (kWh/MWh_th)"] = 0.0

        return kpis
