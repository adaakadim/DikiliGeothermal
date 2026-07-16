"""
scada/system.py
Core SCADA system — orchestrates tag DB, alarms, historian, and subsystems.
"""

import time
import logging
from typing import Optional

from core.config.system_config import SystemConfig
from core.diagnostics.communication_monitor import CommunicationMonitor
from core.diagnostics.auto_recovery import SelfDiagnosticsEngine
from .tag_database import TagDatabase, Tag, TagQuality
from .alarm_manager import AlarmManager, AlarmPriority

logger = logging.getLogger(__name__)


def _tag(tag_id, desc, unit, lo_lo=None, lo=None, hi=None, hi_hi=None, metadata=None) -> Tag:
    return Tag(tag_id, desc, unit,
               lo_lo=lo_lo, lo=lo, hi=hi, hi_hi=hi_hi, metadata=metadata or {})


class SCADASystem:
    """
    Top-level SCADA orchestrator for the Dikili Geothermal DHC plant.

    Responsibilities
    ----------------
    - Maintain the live process tag database
    - Run alarm scan on every tick
    - Expose interfaces to control, analytics and hardware layers
    """

    def __init__(self, config: SystemConfig):
        self.config = config
        self.db = TagDatabase()
        self.alarms = AlarmManager()
        self._running = False
        self._tick_count = 0
        self._start_time: Optional[float] = None

        self.comm_monitor = CommunicationMonitor()
        self.diagnostics_engine = SelfDiagnosticsEngine(self.comm_monitor, self.config)
        self.diagnostics_engine.on_notification = self._on_recovery_notification
        
        self._register_modules()
        self._register_recovery_handlers()

        # Import here to avoid circular imports at module level
        from simulation.plant_simulator import PlantSimulator
        self._simulator = PlantSimulator(config, self.db)

        self._register_tags()
        logger.info("SCADA system initialised — %d tags registered", len(self.db.all_tags()))

    # ── Module Registration ───────────────────────────────────────────────────
    def _register_modules(self):
        # Register core modules with the communication monitor
        self.comm_monitor.register_module("SCADA Core", interval=self.config.scan_interval)
        self.comm_monitor.register_module("Tag Database", interval=self.config.scan_interval)
        self.comm_monitor.register_module("Alarm Manager", interval=self.config.scan_interval)
        self.comm_monitor.register_module("Historian", interval=self.config.historian_flush_interval)
        self.comm_monitor.register_module("AI Engine", interval=self.config.scan_interval)
        self.comm_monitor.register_module("Digital Twin", interval=self.config.scan_interval)
        self.comm_monitor.register_module("Simulation Engine", interval=self.config.scan_interval)
        self.comm_monitor.register_module("Sensor Manager", interval=self.config.scan_interval)
        self.comm_monitor.register_module("Decision Support", interval=self.config.scan_interval)
        self.comm_monitor.register_module("Configuration Manager", interval=60.0)

    def _on_recovery_notification(self, level: str, message: str):
        # Route notifications to alarm manager as INFO/WARN events if needed, 
        # or just let it be handled by the UI event log via ALARM events.
        priority = AlarmPriority.LOW if level == "INFO" else (AlarmPriority.MEDIUM if level == "WARN" else AlarmPriority.HIGH)
        # Avoid spamming active alarms if it's just INFO, so we just log it or raise a transient alarm.
        if level != "INFO":
            self.alarms.raise_alarm("SYS_RECOVERY", "SYS", message, priority)

    def _register_recovery_handlers(self):
        # Register standard handlers for automatic recovery
        self.diagnostics_engine.register_recovery_handler("Historian", lambda: True) # Simulate successful reconnection
        self.diagnostics_engine.register_recovery_handler("AI Engine", lambda: True) # Simulate successful restart
        self.diagnostics_engine.register_recovery_handler("Tag Database", lambda: True)
        self.diagnostics_engine.register_recovery_handler("Sensor Manager", lambda: True)
        self.diagnostics_engine.register_recovery_handler("Digital Twin", lambda: True)
        self.diagnostics_engine.register_recovery_handler("Simulation Engine", lambda: True)
        self.diagnostics_engine.register_recovery_handler("Decision Support", lambda: True)

    # ── Tag Registration ───────────────────────────────────────────────────────
    def _register_tags(self):
        cfg = self.config

        # Per-well tags
        for well in cfg.wells:
            wid = well.well_id
            self.db.register(_tag(f"{wid}.TEMP",    f"{wid} Wellhead Temperature",     "°C",
                                  lo_lo=cfg.min_wellhead_temp_c - 5,
                                  lo=cfg.min_wellhead_temp_c,
                                  hi=cfg.max_wellhead_temp_c,
                                  hi_hi=cfg.max_wellhead_temp_c + 5))
            self.db.register(_tag(f"{wid}.PRES",    f"{wid} Wellhead Pressure",         "bar",
                                  lo_lo=cfg.min_system_pressure_bar - 0.5,
                                  lo=cfg.min_system_pressure_bar,
                                  hi=cfg.max_system_pressure_bar,
                                  hi_hi=cfg.max_system_pressure_bar + 1))
            self.db.register(_tag(f"{wid}.FLOW",    f"{wid} Production Flow",           "m³/h",
                                  lo_lo=0, lo=cfg.min_flow_m3h,
                                  hi=well.max_flow_m3h,
                                  hi_hi=well.max_flow_m3h * 1.1))
            self.db.register(_tag(f"{wid}.PUMP_ST", f"{wid} Production Pump Status",    ""))
            self.db.register(_tag(f"{wid}.PUMP_SP", f"{wid} Production Pump Setpoint",  "%",
                                  lo_lo=0, lo=10, hi=95, hi_hi=100))

        # Phase 9.7.1.A - Production Wells Engineering Database
        for asset in getattr(cfg, 'production_wells', []):
            pw = asset.asset_id
            
            # Common metadata for engineering tags
            meta_default = {
                "Scan Rate": cfg.scan_interval,
                "Historian Enabled": True,
                "Alarm Enabled": True,
                "AI Enabled": True,
                "Dashboard Visible": True,
                "Digital Twin Visible": True,
                "Trend Enabled": True,
                "Accuracy": "+/- 0.5%",
                "Deadband": "0.1",
                "Asset ID": pw,
                "Asset Type": asset.asset_type
            }

            self.db.register(_tag(f"{pw}.STATUS", f"{pw} Status", "", metadata=meta_default))
            self.db.register(_tag(f"{pw}.TEMP", f"{pw} Temperature", "°C", 
                                  lo_lo=asset.min_temperature_c-10, lo=asset.min_temperature_c, 
                                  hi=asset.max_temperature_c, hi_hi=asset.max_temperature_c+10, metadata=meta_default))
            self.db.register(_tag(f"{pw}.PRES", f"{pw} Pressure", "bar", 
                                  lo_lo=asset.min_pressure_bar-2, lo=asset.min_pressure_bar, 
                                  hi=asset.max_pressure_bar, hi_hi=asset.max_pressure_bar+2, metadata=meta_default))
            self.db.register(_tag(f"{pw}.FLOW", f"{pw} Flow", "m³/h", 
                                  lo_lo=0, lo=asset.min_flow_m3h, hi=asset.max_flow_m3h, hi_hi=asset.max_flow_m3h*1.1, metadata=meta_default))
            self.db.register(_tag(f"{pw}.TOT_FLOW", f"{pw} Totalized Flow", "m³", metadata=meta_default))
            self.db.register(_tag(f"{pw}.OP_HOURS", f"{pw} Operating Hours", "h", metadata=meta_default))
            self.db.register(_tag(f"{pw}.AVAILABILITY", f"{pw} Availability", "%", metadata=meta_default))
            self.db.register(_tag(f"{pw}.LAST_MAINT", f"{pw} Last Maintenance", "", metadata=meta_default))
            self.db.register(_tag(f"{pw}.RES_CONN", f"{pw} Reservoir Connection", "", metadata=meta_default))
            self.db.register(_tag(f"{pw}.HEALTH_IDX", f"{pw} Well Health Index", "%", lo_lo=20, lo=50, metadata=meta_default))
        
        self.db.register(_tag("PROD.TOT_FLOW", "Total Production Flow", "m³/h", metadata={"Historian Enabled": True}))
        self.db.register(_tag("PROD.AVG_TEMP", "Average Production Temperature", "°C", metadata={"Historian Enabled": True}))
        self.db.register(_tag("PROD.AVG_PRES", "Average Production Pressure", "bar", metadata={"Historian Enabled": True}))
        self.db.register(_tag("PROD.TOT_THERMAL", "Total Thermal Production", "MW", metadata={"Historian Enabled": True}))
        self.db.register(_tag("PROD.AVAILABILITY", "Production Availability", "%", metadata={"Historian Enabled": True}))

        # Heat exchanger / plate heat exchanger tags
        self.db.register(_tag("HX.SUPPLY_TEMP",  "HX Primary Supply Temperature",  "°C",
                               lo_lo=40, lo=50, hi=cfg.max_wellhead_temp_c, hi_hi=cfg.max_wellhead_temp_c+5))
        self.db.register(_tag("HX.RETURN_TEMP",  "HX Primary Return Temperature",  "°C"))
        self.db.register(_tag("HX.SEC_SUPPLY",   "HX Secondary Supply Temperature","°C",
                               lo=cfg.target_supply_temp_c - 10,
                               hi=cfg.target_supply_temp_c + 10,
                               hi_hi=cfg.target_supply_temp_c + 15))
        self.db.register(_tag("HX.SEC_RETURN",   "HX Secondary Return Temperature","°C"))
        self.db.register(_tag("HX.EFFICIENCY",   "HX Thermal Efficiency",          "%"))
        self.db.register(_tag("HX.THERMAL_POWER","HX Thermal Power Output",        "MW"))

        # District heating network
        self.db.register(_tag("DH.SUPPLY_PRES",  "DH Network Supply Pressure",     "bar",
                               lo_lo=1.5, lo=2.0, hi=8.0, hi_hi=10.0))
        self.db.register(_tag("DH.RETURN_PRES",  "DH Network Return Pressure",     "bar"))
        self.db.register(_tag("DH.TOTAL_FLOW",   "DH Total Distribution Flow",     "m³/h",
                               lo_lo=0, lo=50, hi=cfg.max_flow_m3h, hi_hi=cfg.max_flow_m3h*1.05))
        self.db.register(_tag("DH.DELTA_T",      "DH Temperature Differential",    "K"))

        # Per-zone tags
        for zone in cfg.zones:
            zid = zone.zone_id
            self.db.register(_tag(f"{zid}.FLOW",       f"{zid} Zone Flow",               "m³/h"))
            self.db.register(_tag(f"{zid}.SUPPLY_T",   f"{zid} Zone Supply Temp",        "°C"))
            self.db.register(_tag(f"{zid}.RETURN_T",   f"{zid} Zone Return Temp",        "°C"))
            self.db.register(_tag(f"{zid}.VALVE_POS",  f"{zid} Zone Control Valve",      "%",
                                  lo_lo=0, lo=5, hi=95, hi_hi=100))

        # Plant totals
        self.db.register(_tag("PLANT.TOTAL_POWER",   "Total Thermal Power Delivered",  "MW"))
        self.db.register(_tag("PLANT.DAILY_ENERGY",  "Daily Energy Delivered",         "MWh"))
        self.db.register(_tag("PLANT.UPTIME_PCT",    "Plant Uptime Today",             "%"))
        self.db.register(_tag("PLANT.ALARM_COUNT",   "Active Alarm Count",             ""))
        self.db.register(_tag("PLANT.COP",           "Plant COP (Coefficient of Perf)",""))

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    def start(self):
        self._running = True
        self._start_time = time.time()
        self._simulator.initialise()
        logger.info("SCADA system STARTED.")

    def stop(self):
        self._running = False
        logger.info("SCADA system STOPPED. Total ticks: %d", self._tick_count)

    def is_running(self) -> bool:
        return self._running

    # ── Main Scan Cycle ───────────────────────────────────────────────────────
    def tick(self):
        self._tick_count += 1

        # 1. Acquire process values (sim or hardware)
        self._simulator.step()

        # 2. Derived calculations
        self._calculate_derived()

        # 3. Alarm scan
        self._scan_alarms()

        # 4. Update plant totals
        self._update_plant_totals()
        
        # 4.5 Evaluate network diagnostics (simulated latency)
        self._simulate_network_diagnostics()
        
        # 4.6 Evaluate Auto Recovery
        self.diagnostics_engine.evaluate()

        # 5. Console display (every 5 ticks to avoid flood)
        if self._tick_count % 5 == 0:
            self._console_display()

    def _simulate_network_diagnostics(self):
        import random
        # Simulate heartbeats for synchronous modules
        modules = [
            "SCADA Core", "Tag Database", "Alarm Manager", "Digital Twin", 
            "Simulation Engine", "Sensor Manager", "Decision Support"
        ]
        
        # AI Engine and Historian might have variable latencies or occasional drops
        for mod in modules:
            # Baseline fast internal memory communication
            latency = random.uniform(0.1, 2.5)
            self.comm_monitor.record_heartbeat(mod, latency)
            
        # Simulate AI Engine (sometimes slower)
        ai_lat = random.uniform(5.0, 45.0)
        if random.random() > 0.05:  # 5% chance of dropped heartbeat
            self.comm_monitor.record_heartbeat("AI Engine", ai_lat)
        else:
            self.comm_monitor.record_error("AI Engine", "dropped")
            
        # Simulate Historian (batch writes, longer latency)
        if self._tick_count % max(1, int(self.config.historian_flush_interval / self.config.scan_interval)) == 0:
            hist_lat = random.uniform(15.0, 120.0)
            self.comm_monitor.record_heartbeat("Historian", hist_lat)
            
        # Config Manager (infrequent)
        if self._tick_count % int(60.0 / self.config.scan_interval) == 0:
            self.comm_monitor.record_heartbeat("Configuration Manager", random.uniform(1.0, 5.0))
            
        self.comm_monitor.evaluate_health()

    # ── Derived Tag Calculations ──────────────────────────────────────────────
    def _calculate_derived(self):
        # Phase 9.7.1.A - Production Wells Aggregation
        production_wells = [asset.asset_id for asset in getattr(self.config, 'production_wells', [])]
        total_flow = 0.0
        sum_temp = 0.0
        sum_pres = 0.0
        sum_avail = 0.0
        active_wells = 0
        
        for pw in production_wells:
            flow = self.db.read_value(f"{pw}.FLOW", 0.0)
            if flow is None: flow = 0.0
            
            temp = self.db.read_value(f"{pw}.TEMP", 0.0)
            if temp is None: temp = 0.0
            
            pres = self.db.read_value(f"{pw}.PRES", 0.0)
            if pres is None: pres = 0.0
            
            avail = self.db.read_value(f"{pw}.AVAILABILITY", 0.0)
            if avail is None: avail = 0.0
            
            total_flow += flow
            if flow > 0:
                sum_temp += temp * flow
                sum_pres += pres * flow
                active_wells += 1
            sum_avail += avail

        avg_temp = 0.0
        avg_pres = 0.0
        if total_flow > 0:
            avg_temp = sum_temp / total_flow
            avg_pres = sum_pres / total_flow
            
        avg_avail = 0.0
        if len(production_wells) > 0:
            avg_avail = sum_avail / len(production_wells)

        self.db.write("PROD.TOT_FLOW", round(total_flow, 2))
        self.db.write("PROD.AVG_TEMP", round(avg_temp, 2))
        self.db.write("PROD.AVG_PRES", round(avg_pres, 2))
        self.db.write("PROD.AVAILABILITY", round(avg_avail, 2))
        
        # Simple thermal calculation Q = m_dot * Cp * deltaT, assuming ref temp 20C
        # kg/s = total_flow * 1000 / 3600
        # Cp = 4.186 kJ/(kg*K)
        ref_temp = 20.0
        if total_flow > 0 and avg_temp > ref_temp:
            mass_flow = total_flow * 1000.0 / 3600.0
            power_mw = (mass_flow * 4.186 * (avg_temp - ref_temp)) / 1000.0
            self.db.write("PROD.TOT_THERMAL", round(power_mw, 2))
        else:
            self.db.write("PROD.TOT_THERMAL", 0.0)

        supply = self.db.read_value("HX.SEC_SUPPLY", 0.0)
        ret    = self.db.read_value("HX.SEC_RETURN", 0.0)
        flow   = self.db.read_value("DH.TOTAL_FLOW", 0.0)

        delta_t = supply - ret
        self.db.write("DH.DELTA_T", round(delta_t, 2))

        # Q = m_dot * Cp * Delta_T   (water Cp ≈ 4.186 kJ/kg·K, density ≈ 1 kg/L)
        # flow in m³/h → kg/s = flow * 1000 / 3600
        if flow > 0 and delta_t > 0:
            mass_flow_kgs = flow * 1000.0 / 3600.0
            power_kw = mass_flow_kgs * 4.186 * delta_t
            power_mw = power_kw / 1000.0
        else:
            power_mw = 0.0

        self.db.write("HX.THERMAL_POWER", round(power_mw, 3))
        self.db.write("PLANT.TOTAL_POWER", round(power_mw, 3))

        # HX efficiency (simplified ratio of secondary to primary delta-T)
        primary_in  = self.db.read_value("HX.SUPPLY_TEMP", 1.0)
        primary_out = self.db.read_value("HX.RETURN_TEMP", 0.0)
        if (primary_in - primary_out) > 0:
            eff = delta_t / (primary_in - primary_out) * 100.0
            self.db.write("HX.EFFICIENCY", round(min(eff, 100.0), 1))

    def _update_plant_totals(self):
        self.db.write("PLANT.ALARM_COUNT", len(self.alarms.active_alarms))

        if self._start_time:
            uptime = (time.time() - self._start_time) / 3600.0  # hours
            power  = self.db.read_value("PLANT.TOTAL_POWER", 0.0)
            energy = power * (self.config.scan_interval / 3600.0)  # incremental MWh
            prev   = self.db.read_value("PLANT.DAILY_ENERGY", 0.0) or 0.0
            self.db.write("PLANT.DAILY_ENERGY", round(prev + energy, 4))
            self.db.write("PLANT.UPTIME_PCT",   min(100.0, round(uptime / 24.0 * 100, 1)))

    # ── Alarm Scan ────────────────────────────────────────────────────────────
    def _scan_alarms(self):
        for tag_id, tag in self.db.all_tags().items():
            state = tag.alarm_state
            alarm_key = f"TAG_{tag_id}"

            if state in ("HI_HI", "LO_LO"):
                priority = AlarmPriority.CRITICAL if "TEMP" in tag_id or "PRES" in tag_id else AlarmPriority.HIGH
                self.alarms.raise_alarm(
                    alarm_key,
                    tag_id,
                    f"{tag.description} {state}: {tag.value} {tag.unit}",
                    priority,
                )
            elif state in ("HI", "LO"):
                self.alarms.raise_alarm(
                    alarm_key,
                    tag_id,
                    f"{tag.description} {state}: {tag.value} {tag.unit}",
                    AlarmPriority.MEDIUM,
                )
            else:
                self.alarms.clear_alarm(alarm_key)

    # ── Console Display ───────────────────────────────────────────────────────
    def _console_display(self):
        sep = "═" * 62
        print(f"\n{sep}")
        print(f"  🌋  DikiliGeothermal SCADA  |  Tick #{self._tick_count}")
        print(sep)

        # Wells
        for well in self.config.wells:
            wid = well.well_id
            t  = self.db.read_value(f"{wid}.TEMP", "N/A")
            p  = self.db.read_value(f"{wid}.PRES", "N/A")
            fl = self.db.read_value(f"{wid}.FLOW", "N/A")
            st = self.db.read_value(f"{wid}.PUMP_ST", "N/A")
            print(f"  {wid} [{well.name}]")
            print(f"     Temp: {t:>7.2f} °C  |  Press: {p:>6.2f} bar  |  Flow: {fl:>6.1f} m³/h  |  Pump: {st}")

        print()
        # Heat exchanger
        hs  = self.db.read_value("HX.SEC_SUPPLY", 0)
        hr  = self.db.read_value("HX.SEC_RETURN", 0)
        hxp = self.db.read_value("HX.THERMAL_POWER", 0)
        hxe = self.db.read_value("HX.EFFICIENCY", 0)
        print(f"  Heat Exchanger:  Supply {hs:.1f}°C  |  Return {hr:.1f}°C  |  {hxp:.2f} MW  |  Eff {hxe:.1f}%")

        # Network
        dhp = self.db.read_value("DH.SUPPLY_PRES", 0)
        dhf = self.db.read_value("DH.TOTAL_FLOW", 0)
        ddt = self.db.read_value("DH.DELTA_T", 0)
        print(f"  DH Network   :  Press {dhp:.2f} bar  |  Flow {dhf:.1f} m³/h  |  ΔT {ddt:.1f} K")

        print()
        tp = self.db.read_value("PLANT.TOTAL_POWER", 0)
        te = self.db.read_value("PLANT.DAILY_ENERGY", 0)
        ac = self.db.read_value("PLANT.ALARM_COUNT", 0)
        print(f"  🔋 Power: {tp:.2f} MW  |  Daily Energy: {te:.3f} MWh  |  🔔 Alarms: {ac}")

        if self.alarms.active_alarms:
            print()
            n       = len(self.alarms.active_alarms)
            crit    = self.alarms.critical_active
            hdr_tag = "*** CRITICAL ***" if crit else "! WARNING !"
            print(f"  [{hdr_tag}]  {n} ACTIVE ALARM{'S' if n != 1 else ''}  [{hdr_tag}]")
            print(f"  {'TYPE':<12} {'WELL':<8} {'DESCRIPTION':<40} {'PRI':<10} {'AGE':>6}")
            print(f"  {'-'*12} {'-'*8} {'-'*40} {'-'*10} {'-'*6}")
            for alarm in self.alarms.active_alarms[:8]:
                aid = alarm.alarm_id.upper()
                if ".TEMP." in aid:
                    atype = "[HIGH TEMP]"
                elif ".PRES." in aid:
                    atype = "[LOW PRES ]"
                elif ".FLOW." in aid:
                    atype = "[FLOW FAIL]"
                elif ".PUMP." in aid:
                    atype = "[PUMP RISK]"
                else:
                    atype = "[SENSOR   ]"
                age_s   = int(alarm.age_seconds)
                age_str = f"{age_s // 60:02d}:{age_s % 60:02d}"
                desc    = alarm.description[:40]
                tag     = alarm.tag_id[:7]
                print(f"  {atype:<12} {tag:<8} {desc:<40} {alarm.priority.name:<10} {age_str:>6}")
            if n > 8:
                print(f"  ... and {n - 8} more alarm(s) not shown.")
        else:
            print()
            print("  [OK] ALARM STATUS: NO ACTIVE ALARMS -- ALL SYSTEMS NOMINAL")
            categories = ["HIGH TEMP", "LOW PRESSURE", "FLOW FAILURE", "PUMP FAILURE RISK"]
            print("  ALL CLEAR: " + "  |  ".join(f"[{c}]" for c in categories))

        print(sep)

