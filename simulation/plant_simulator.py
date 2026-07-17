"""
simulation/plant_simulator.py
Physics-based geothermal district heating plant simulator.
Provides realistic, time-varying sensor readings with noise and thermodynamic consistency.
"""

import math
import random
import time
import logging
from typing import Dict

from core.config.system_config import SystemConfig
from scada.tag_database import TagDatabase
from simulation.models.operating_modes import PlantMode, ModeManager

logger = logging.getLogger(__name__)

class PlantSimulator:
    def __init__(self, config: SystemConfig, db: TagDatabase):
        self.config = config
        self.db = db
        self.mode_manager = ModeManager()
        self._t0 = time.time()
        self._last_t = self._t0
        self._well_state: Dict[str, dict] = {}
        self._pump_state: Dict[str, dict] = {}
        self._hx_fouling = 4.5
        self._sep_level = 50.0
        self._load_factor = 0.75

    def set_mode(self, mode: PlantMode, target: str = None):
        """Allows external systems to change the active plant mode."""
        self.mode_manager.set_mode(mode, target)
        logger.info(f"Plant mode changed to {mode.value} targeting {target}")

    def initialise(self):
        for well in self.config.wells:
            self._well_state[well.well_id] = {
                "temp": well.reservoir_temp_c,
                "pres": well.nominal_pressure_bar,
                "flow": well.max_flow_m3h * 0.70,
            }
            # Also init pump state for W-01 etc
            wid = well.well_id
            suffix = wid.split("-")[-1]
            try:
                p_id = f"P-10{int(suffix)}"
            except ValueError:
                p_id = f"P-{suffix}"
            self._pump_state[p_id] = {
                "brg_temp": 45.0,
                "wear": 0.0
            }
            
        for pw in getattr(self.config, 'production_wells', []):
            self._well_state[pw.asset_id] = {
                "temp": pw.nominal_temperature_c,
                "pres": pw.nominal_pressure_bar,
                "flow": pw.design_flow_m3h * 0.75,
                "tot_flow": 0.0,
                "op_hours": pw.operating_hours,
            }
            self._pump_state[pw.asset_id] = {
                "brg_temp": 45.0,
                "wear": 0.0
            }
            
        # Common pumps
        self._pump_state["DH_PUMP"] = {"brg_temp": 40.0, "wear": 0.0}
        self._pump_state["INJ_PUMP"] = {"brg_temp": 45.0, "wear": 0.0}

        logger.info("Plant simulator initialized with engineering-grade thermodynamic model.")

    def step(self):
        now = time.time()
        dt = max(now - self._last_t, 1.0)
        self._last_t = now
        elapsed = now - self._t0
        
        # Demand Cycle: Calibrated dual-peak daily profile
        tod = elapsed % 86400
        morning_peak = 0.30 * math.exp(-((tod - 25200.0) ** 2) / (2.0 * 7200.0 ** 2))
        evening_peak = 0.25 * math.exp(-((tod - 68400.0) ** 2) / (2.0 * 10800.0 ** 2))
        base_load = 0.40 + morning_peak + evening_peak
        
        self._load_factor = self.mode_manager.get_load_factor_override(base_load)
        
        total_flow = 0.0
        weighted_temp = 0.0
        total_max_flow = sum(w.max_flow_m3h for w in self.config.wells)
        target_total_flow = total_max_flow * self._load_factor

        # ── Production Wells & Pumps ──
        for well in self.config.wells:
            wid = well.well_id
            suffix = wid.split("-")[-1]
            try:
                p_id = f"P-10{int(suffix)}"
                v_id = f"V-10{int(suffix)}"
            except ValueError:
                p_id = f"P-{suffix}"
                v_id = f"V-{suffix}"
                
            ws = self._well_state[wid]
            ps = self._pump_state[p_id]

            target_flow = target_total_flow * (well.max_flow_m3h / total_max_flow)
            target_flow = self.mode_manager.get_flow_target(p_id, target_flow)
            
            ws["flow"] = self._inertia(ws["flow"], target_flow, dt, tau=30.0)
            
            k_drawdown = 0.0001
            target_pres = well.nominal_pressure_bar - k_drawdown * (ws["flow"] ** 2)
            ws["pres"] = self._inertia(ws["pres"], target_pres, dt, tau=10.0)
            
            heat_loss_k = 25.0
            res_temp = self.mode_manager.get_reservoir_temp_override(well.reservoir_temp_c)
            if ws["flow"] > 5.0:
                target_temp = res_temp - (heat_loss_k / ws["flow"])
            else:
                target_temp = res_temp - 10.0
            ws["temp"] = self._inertia(ws["temp"], target_temp, dt, tau=120.0)
            
            enthalpy = ws["temp"] * 4.18 
            
            flow_ratio = ws["flow"] / well.max_flow_m3h
            pump_eff = 0.78 - 0.1 * (flow_ratio - 0.8)**2
            if pump_eff < 0.4: pump_eff = 0.4
            
            # Pump failure mode overrides efficiency
            if self.mode_manager.current_mode == PlantMode.PUMP_FAILURE and self.mode_manager.target_equipment == p_id:
                pump_eff = pump_eff * 0.5
            
            hydraulic_head = 250.0
            hydraulic_power = (ws["flow"] * hydraulic_head) / (367.0 * pump_eff)
            pump_power = hydraulic_power / 0.95
            pump_voltage = 690.0
            pump_current = pump_power * 1000.0 / (math.sqrt(3) * pump_voltage * 0.85)
            pump_rpm = max(1400.0, min(2950.0, 2900.0 * flow_ratio)) if ws["flow"] > 1.0 else 0.0
            
            heat_gen = pump_power * 0.05
            heat_diss = 0.02 * (ps["brg_temp"] - 25.0)
            ps["brg_temp"] += (heat_gen - heat_diss) * dt * 0.01
            
            wear_rate = self.mode_manager.get_pump_wear_rate(p_id, 1e-8)
            ps["wear"] += (ps["brg_temp"] - 40.0) * dt * wear_rate if ps["brg_temp"] > 40.0 else 0
            
            pump_vib = 1.0 + (flow_ratio)**2 * 0.5 + ps["wear"] * 5.0
            if pump_rpm == 0.0: pump_vib = 0.0
            
            valve_pos = flow_ratio * 100.0
            valve_dp = (flow_ratio)**2 * 0.8
            
            # Maintenance check
            status = "MAINTENANCE" if self.mode_manager.current_mode == PlantMode.MAINTENANCE and self.mode_manager.target_equipment == p_id else ("RUNNING" if ws["flow"] > 5.0 else "STANDBY")
            
            self.db.write(f"{wid}.TEMP", round(ws["temp"] + self._noise(0.1), 2))
            self.db.write(f"{wid}.PRES", round(ws["pres"] + self._noise(0.05), 2))
            self.db.write(f"{wid}.FLOW", round(max(ws["flow"] + self._noise(0.5), 0.0), 1))
            self.db.write(f"{wid}.ENTHALPY", round(enthalpy, 1))
            
            self.db.write(f"{p_id}.CURRENT", round(pump_current + self._noise(0.5), 1) if pump_rpm > 0 else 0.0)
            self.db.write(f"{p_id}.Motor Current (A)", round(pump_current + self._noise(0.5), 1) if pump_rpm > 0 else 0.0)
            self.db.write(f"{p_id}.VOLTAGE", round(pump_voltage + self._noise(1.0), 1) if pump_rpm > 0 else 0.0)
            self.db.write(f"{p_id}.POWER", round(pump_power + self._noise(0.2), 1) if pump_rpm > 0 else 0.0)
            self.db.write(f"{p_id}.Power (kW)", round(pump_power + self._noise(0.2), 1) if pump_rpm > 0 else 0.0)
            self.db.write(f"{p_id}.EFF", round(pump_eff * 100.0, 1) if pump_rpm > 0 else 0.0)
            self.db.write(f"{p_id}.RPM", round(pump_rpm, 0))
            self.db.write(f"{p_id}.VIB", round(pump_vib + self._noise(0.05), 2) if pump_rpm > 0 else 0.0)
            self.db.write(f"{p_id}.BRG_TEMP", round(ps["brg_temp"] + self._noise(0.2), 1))
            
            # Stop accumulation in maintenance
            if status != "MAINTENANCE" and pump_rpm > 0:
                runtime_inc = dt / 3600.0
            else:
                runtime_inc = 0.0
            
            # We don't have a specific state for runtime for non-asset wells, just mock it
            self.db.write(f"{p_id}.RUNTIME", round(elapsed / 3600.0 + 5000.0, 1)) # Still mocking this one
            self.db.write(f"{p_id}.STATUS", status)
            
            self.db.write(f"{v_id}.VALVE_POS", round(valve_pos + self._noise(0.1), 1))
            self.db.write(f"{v_id}.VALVE_DP", round(valve_dp + self._noise(0.01), 2))
            
            flow_pos = max(ws["flow"], 0.0)
            total_flow += flow_pos
            weighted_temp += ws["temp"] * flow_pos

        # Phase 9.7.1.A - Production Wells Simulation
        for pw in getattr(self.config, 'production_wells', []):
            pid = pw.asset_id
            ws = self._well_state[pid]
            ps = self._pump_state[pid]
            
            target_flow = pw.design_flow_m3h * self._load_factor
            target_flow = self.mode_manager.get_flow_target(pid, target_flow)
            
            ws["flow"] = self._inertia(ws["flow"], target_flow, dt, tau=30.0)
            if self.mode_manager.current_mode != PlantMode.EMERGENCY_SHUTDOWN and self.mode_manager.target_equipment != pid:
                ws["flow"] = max(pw.min_flow_m3h * 0.9, min(ws["flow"], pw.max_flow_m3h * 1.1))
            else:
                ws["flow"] = max(0.0, min(ws["flow"], pw.max_flow_m3h * 1.1)) # Can drop to 0
            
            k_drawdown = 0.0001
            target_pres = pw.nominal_pressure_bar - k_drawdown * (ws["flow"] ** 2)
            ws["pres"] = self._inertia(ws["pres"], target_pres, dt, tau=10.0)
            
            heat_loss_k = 25.0
            res_temp = self.mode_manager.get_reservoir_temp_override(pw.nominal_temperature_c)
            if ws["flow"] > 5.0:
                target_temp = res_temp - (heat_loss_k / ws["flow"])
            else:
                target_temp = res_temp - 10.0
            ws["temp"] = self._inertia(ws["temp"], target_temp, dt, tau=120.0)
            
            status = "MAINTENANCE" if self.mode_manager.current_mode == PlantMode.MAINTENANCE and self.mode_manager.target_equipment == pid else ("ACTIVE" if ws["flow"] > 5.0 else "STANDBY")
            
            if status != "MAINTENANCE" and ws["flow"] > 5.0:
                inc_flow = ws["flow"] * (dt / 3600.0)
                ws["tot_flow"] += inc_flow
                ws["op_hours"] += dt / 3600.0
            
            self.db.write(f"{pid}.FLOW", round(ws["flow"] + self._noise(0.5), 1))
            self.db.write(f"{pid}.TEMP", round(ws["temp"] + self._noise(0.1), 2))
            self.db.write(f"{pid}.PRES", round(ws["pres"] + self._noise(0.05), 2))
            self.db.write(f"{pid}.TOT_FLOW", round(ws["tot_flow"], 1))
            self.db.write(f"{pid}.OP_HOURS", round(ws["op_hours"], 1))
            self.db.write(f"{pid}.AVAILABILITY", pw.availability_pct)
            self.db.write(f"{pid}.STATUS", status)
            
            total_flow += max(ws["flow"], 0.0)
            weighted_temp += ws["temp"] * max(ws["flow"], 0.0)
        
        # ── Separator (SEP-01) ──
        avg_geo_temp = (weighted_temp / total_flow) if total_flow > 0 else 95.0
        sep_pres = 1.5 + (total_flow / total_max_flow) * 1.0
        # Separator Steam Fraction (Flash thermodynamic approximation)
        # Saturated temperature at sep_pres (very rough approximation: 100C at 1 bar + ~15C per bar)
        sat_temp = 100.0 + sep_pres * 15.0
        sep_steam_frac = max(0.0, (avg_geo_temp - sat_temp) * 0.04)
        
        target_level = 50.0 + (total_flow / total_max_flow - 0.5) * 5.0
        self._sep_level = self._inertia(self._sep_level, target_level, dt, tau=60.0)
        
        self.db.write("SEP.PRES", round(sep_pres + self._noise(0.05), 2))
        self.db.write("SEP.STEAM_FRAC", round(sep_steam_frac + self._noise(0.01), 2))
        self.db.write("SEP.BRINE_TEMP", round(avg_geo_temp + self._noise(0.1), 2))
        self.db.write("SEP.LEVEL", round(self._sep_level + self._noise(0.5), 1))
        
        # ── Heat Exchanger (HX-101) ──
        fouling_rate = self.mode_manager.get_hx_fouling_rate(0.0005)
        self._hx_fouling += dt / (24*3600) * fouling_rate
        hx_eff = max(0.60, 0.95 - self._hx_fouling * 0.02)
        hx_dp = 0.5 + (total_flow / total_max_flow)**2 * 1.0 + self._hx_fouling * 0.02
        
        dh_target_supply = 82.0
        dh_target_return = dh_target_supply - 35.0 * self._load_factor
        
        hx_dh_supply = dh_target_return + (avg_geo_temp - dh_target_return) * hx_eff
        hx_dh_return = dh_target_return
        hx_geo_outlet = avg_geo_temp - (hx_dh_supply - hx_dh_return) * 0.98
        hx_heat_rate = total_flow * 1.139 * (avg_geo_temp - hx_geo_outlet) / 1000.0
        
        self.db.write("HX.EFF", round(hx_eff * 100.0, 1))
        self.db.write("HX.FOULING", round(self._hx_fouling, 3))
        self.db.write("HX.PRES_DROP", round(hx_dp + self._noise(0.01), 2))
        self.db.write("HX.HEAT_RATE", round(hx_heat_rate + self._noise(0.2), 2))
        self.db.write("HX.SUPPLY_TEMP", round(avg_geo_temp + self._noise(0.1), 2))
        self.db.write("HX.RETURN_TEMP", round(hx_geo_outlet + self._noise(0.1), 2))
        self.db.write("HX.SEC_SUPPLY", round(hx_dh_supply + self._noise(0.1), 2))
        self.db.write("HX.SEC_RETURN", round(hx_dh_return + self._noise(0.1), 2))
        
        # ── DH Network & Circulation Pump (DH_PUMP) ──
        dh_flow = total_flow * 0.98
        dh_pres_diff = 2.0 + (dh_flow / total_max_flow)**2 * 1.0
        
        dh_pump_power = (dh_flow * (dh_pres_diff * 10.2)) / (367.0 * 0.82)
        dh_pump_current = dh_pump_power * 1000.0 / (math.sqrt(3) * 400.0 * 0.85)
        dh_pump_rpm = max(700.0, min(1500.0, 1450.0 * (dh_flow / total_max_flow))) if dh_flow > 1.0 else 0.0
        
        ps_dh = self._pump_state["DH_PUMP"]
        heat_gen = dh_pump_power * 0.05
        heat_diss = 0.02 * (ps_dh["brg_temp"] - 25.0)
        ps_dh["brg_temp"] += (heat_gen - heat_diss) * dt * 0.01
        wear_rate_dh = self.mode_manager.get_pump_wear_rate("DH_PUMP", 1e-8)
        ps_dh["wear"] += (ps_dh["brg_temp"] - 40.0) * dt * wear_rate_dh if ps_dh["brg_temp"] > 40.0 else 0
        dh_pump_vib = 1.0 + (dh_flow / (total_max_flow*0.6))**2 * 0.3 + ps_dh["wear"] * 5.0
        if dh_pump_rpm == 0.0: dh_pump_vib = 0.0
        
        self.db.write("DH.TOTAL_FLOW", round(max(dh_flow + self._noise(1.0), 0.0), 1))
        self.db.write("DH.SUPPLY_PRES", round(dh_pres_diff + 2.0 + self._noise(0.05), 2))
        self.db.write("DH.RETURN_PRES", 2.0 + self._noise(0.01))
        self.db.write("DH.HEAT_FLOW", round(hx_heat_rate * 0.98 + self._noise(0.2), 2))
        self.db.write("DH.DIFF_PRES", round(dh_pres_diff + self._noise(0.05), 2))
        self.db.write("DH_PUMP.CURRENT", round(dh_pump_current + self._noise(0.5), 1) if dh_pump_rpm > 0 else 0.0)
        self.db.write("DH_PUMP.VOLTAGE", round(400.0 + self._noise(1.0), 1) if dh_pump_rpm > 0 else 0.0)
        self.db.write("DH_PUMP.POWER", round(dh_pump_power + self._noise(0.1), 1) if dh_pump_rpm > 0 else 0.0)
        self.db.write("DH_PUMP.EFF", round(82.0, 1) if dh_pump_rpm > 0 else 0.0)
        self.db.write("DH_PUMP.RPM", round(dh_pump_rpm, 0))
        self.db.write("DH_PUMP.VIB", round(dh_pump_vib + self._noise(0.02), 2) if dh_pump_rpm > 0 else 0.0)
        self.db.write("DH_PUMP.BRG_TEMP", round(ps_dh["brg_temp"] + self._noise(0.1), 1))
        
        total_zone_flow = max(dh_flow, 1.0)
        for i, zone in enumerate(self.config.zones):
            zid = zone.zone_id
            share = zone.design_load_mw / sum(z.design_load_mw for z in self.config.zones)
            z_flow = total_zone_flow * share
            z_sup  = hx_dh_supply - i * 0.5
            z_ret  = dh_target_return
            z_vlv  = share * 100.0 * self._load_factor

            self.db.write(f"{zid}.FLOW",      round(max(z_flow + self._noise(0.5), 0.0), 1))
            self.db.write(f"{zid}.SUPPLY_T",  round(z_sup + self._noise(0.1), 2))
            self.db.write(f"{zid}.RETURN_T",  round(z_ret + self._noise(0.1), 2))
            self.db.write(f"{zid}.VALVE_POS", round(min(max(z_vlv, 0.0), 100.0), 1))
            
        # ── Reinjection (INJ_PUMP, INJ_WELL) ──
        inj_flow = total_flow * (1.0 - sep_steam_frac * 0.01)
        inj_pres = 8.0 + (inj_flow / total_max_flow)**2 * 4.0
        inj_temp = hx_geo_outlet - 1.5
        
        inj_pump_power = (inj_flow * (inj_pres * 10.2)) / (367.0 * 0.75)
        inj_pump_current = inj_pump_power * 1000.0 / (math.sqrt(3) * 400.0 * 0.85)
        inj_pump_rpm = max(1400.0, min(2950.0, 2900.0 * (inj_flow / total_max_flow))) if inj_flow > 1.0 else 0.0
        
        ps_inj = self._pump_state["INJ_PUMP"]
        heat_gen = inj_pump_power * 0.05
        heat_diss = 0.02 * (ps_inj["brg_temp"] - 25.0)
        ps_inj["brg_temp"] += (heat_gen - heat_diss) * dt * 0.01
        wear_rate_inj = self.mode_manager.get_pump_wear_rate("INJ_PUMP", 1e-8)
        ps_inj["wear"] += (ps_inj["brg_temp"] - 40.0) * dt * wear_rate_inj if ps_inj["brg_temp"] > 40.0 else 0
        inj_pump_vib = 1.0 + (inj_flow / (total_max_flow*0.5))**2 * 0.6 + ps_inj["wear"] * 5.0
        if inj_pump_rpm == 0.0: inj_pump_vib = 0.0
        
        self.db.write("INJ.FLOW", round(max(inj_flow + self._noise(1.0), 0.0), 1))
        self.db.write("INJ.PRES", round(inj_pres + self._noise(0.05), 2))
        self.db.write("INJ.TEMP", round(inj_temp + self._noise(0.1), 2))
        self.db.write("INJ_PUMP.CURRENT", round(inj_pump_current + self._noise(0.5), 1) if inj_pump_rpm > 0 else 0.0)
        self.db.write("INJ_PUMP.VOLTAGE", round(400.0 + self._noise(1.0), 1) if inj_pump_rpm > 0 else 0.0)
        self.db.write("INJ_PUMP.POWER", round(inj_pump_power + self._noise(0.2), 1) if inj_pump_rpm > 0 else 0.0)
        self.db.write("INJ_PUMP.EFF", round(75.0, 1) if inj_pump_rpm > 0 else 0.0)
        self.db.write("INJ_PUMP.RPM", round(inj_pump_rpm, 0))
        self.db.write("INJ_PUMP.VIB", round(inj_pump_vib + self._noise(0.05), 2) if inj_pump_rpm > 0 else 0.0)
        self.db.write("INJ_PUMP.BRG_TEMP", round(ps_inj["brg_temp"] + self._noise(0.1), 1))

    @staticmethod
    def _noise(sigma: float) -> float:
        return random.gauss(0.0, sigma)

    @staticmethod
    def _inertia(current: float, target: float, dt: float, tau: float) -> float:
        """Physical inertia using a low-pass filter (exponential smoothing)."""
        alpha = dt / (tau + dt)
        return current + alpha * (target - current)
