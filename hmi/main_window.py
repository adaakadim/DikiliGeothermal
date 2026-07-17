"""
gui/app.py
==========
Main graphical SCADA application for the Dikili Geothermal plant.

Assembles the process diagram, KPI cards, trend charts, equipment tree,
event log, and alarm panel into a single professional-grade 1920x1080
dark-themed window.

Run directly:
    python -m gui.app
"""

from __future__ import annotations

import sys
import time
import math
import random
import logging
import tkinter as tk
import tkinter.ttk as ttk
from datetime import datetime

from core.reliability.reliability_manager import reliability_manager, SubsystemStatus

# Force UTF-8 on Windows console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from simulation.sensors import create_well_array, SensorReading
from analytics.fault_detector import FaultDetector, SystemHealth
from scada.alarm_manager import AlarmManager, AlarmPriority

from gui.theme import (
    BG_PRIMARY, BG_SECONDARY, BG_TERTIARY, BG_HEADER, BORDER, BORDER_LIGHT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    CLR_NORMAL, CLR_WARNING, CLR_CRITICAL, CLR_OFFLINE,
    FONT_TITLE, FONT_SUBTITLE, FONT_LABEL, FONT_LABEL_SM,
    FONT_HEADER_BAR, FONT_MONO_MD, FONT_MONO_SM, FONT_MONO_LG,
    REFRESH_MS, status_color, value_color,
)
from gui.widgets import KPICard, PumpIcon, ValveIcon, StatusIndicator
from gui.i18n import tr, CURRENT_LANG, set_locale_preference

from gui.alarm_panel import AlarmPanel
from gui.trend_charts import TrendChartPanel
from gui.panels import EventLogPanel, EquipmentTreePanel
from gui.ai_panel import AIAnalyticsPanel, AIEventLogPanel
from gui.performance_panel import AIPerformancePanel

from analytics.ai.prediction_history import PredictionHistoryLogger
from analytics.ai.confidence_monitor import ConfidenceMonitor
from analytics.ai.feature_importance import FeatureAnalyzer
from analytics.ai.health_index import HealthIndexEngine
from analytics.ai.maintenance_engine import MaintenanceEngine
from analytics.ai.trend_analysis import TrendAnalyzer
from analytics.ai.decision_analyzer import DecisionAnalyzer
from analytics.ai.decision_timeline_logger import DecisionTimelineLogger

from gui.advanced_ai_panel import AdvancedAICenterPanel
from gui.prediction_history_panel import PredictionHistoryPanel
from gui.ai_model_info_panel import AIModelInfoPanel
from gui.ai_dataset_panel import AIDatasetPanel
from gui.ai_decision_timeline_panel import AIDecisionTimelinePanel
from gui.reliability_dashboard import ReliabilityDashboard
from core.diagnostics.auto_recovery import SelfDiagnosticsEngine

logger = logging.getLogger(__name__)

# ─── Process alarm thresholds ─────────────────────────────────────────────────
_T_HI_HI = 109.0;  _T_HI = 105.0;  _T_LO = 78.0;  _T_LO_LO = 72.0
_P_LO_LO = 3.5;    _P_LO = 4.5
_Q_LO_LO = 55.0;   _Q_LO = 80.0
_RISK_WARN = 40.0;  _RISK_CRIT = 70.0


class SCADAGuiApp:
    def __init__(self, well_ids: list[str] = None, scan_interval: int = REFRESH_MS):
        if not well_ids: well_ids = ["W-01", "W-02", "W-03"]
        self._well_ids  = well_ids
        self._interval  = scan_interval
        self._cycle     = 0
        self._start_time = time.time()
        
        # Build the root window but hide it during initialization
        self._root = tk.Tk()
        self._root.withdraw()
        
        from gui.splash_screen import SplashScreen
        self._splash = SplashScreen(self._root, version="1.0.0 Release Candidate")
        self._splash.update_progress(10, "Loading system configuration...")
        
        # Restore SCADASystem to pipeline
        from scada.system import SCADASystem
        from core.config.system_config import SystemConfig
        config = SystemConfig.load()
        self._scada = SCADASystem(config)
        config.system = self._scada  # Provide backward compat
        self._scada.start()
        
        # Use SCADASystem's components
        self._alarms = self._scada.alarms
        self._detector = FaultDetector()
        
        # We can still keep provider for readings mapping or use SCADA
        from core.connectivity.simulator_provider import SimulatorDataProvider
        self._provider = SimulatorDataProvider(well_ids=well_ids)
        self._provider.connect()
        self._wells = self._provider._wells

        # Simulated state
        self._hx_eff   = 85.0
        self._hx_power = 0.0
        self._dh_flow  = 0.0
        self._dh_dt    = 0.0

        # AI State
        self._splash.update_progress(30, "Initializing AI Subsystems...")
        from analytics.ai.feature_engineering import FeatureEngineer
        self._feature_engineer = FeatureEngineer(window_size=5)
        self._last_ai_status = "NORMAL"
        
        # AI Performance Trackers (Phase 3.5 & 4)
        self._history_logger = PredictionHistoryLogger()
        self._confidence_monitor = ConfidenceMonitor()
        self._feature_analyzer = FeatureAnalyzer()
        self._decision_timeline = DecisionTimelineLogger()
        # Phase 4 Advanced Analytics
        self._health_engine = HealthIndexEngine()
        self._maintenance_engine = MaintenanceEngine()
        self._trend_analyzer = TrendAnalyzer(window_size=20)
        
        # Phase 5 & 6 Digital Twin & XAI
        from digital_twin.plant_model.facility import DikiliFacility
        from analytics.ai.shap_explainer import AIExplainer
        from scada.report_generator import ReportGenerator
        from core.historian.historian import DataHistorian
        from core.diagnostics.diagnostics_service import DiagnosticsService
        from analytics.ai.rul.rul_engine import RULEngine
        from analytics.optimization.optimization_engine import OptimizationEngine
        from analytics.anomaly_detection.anomaly_engine import AnomalyEngine
        
        self._splash.update_progress(60, "Loading Digital Twin Models...")
        self._facility = DikiliFacility()
        self._explainer = AIExplainer()
        self._report_generator = ReportGenerator()
        
        from scada.enterprise_report_generator import EnterpriseReportGenerator
        self._enterprise_report_generator = EnterpriseReportGenerator()
        
        self._historian = DataHistorian()
        self._diag_service = DiagnosticsService()
        self._rul_engine = RULEngine(update_interval_hours=0.5)  # Simulate 30 mins per tick for demonstration
        self._opt_engine = OptimizationEngine()
        self._anomaly_engine = AnomalyEngine()
        
        # Phase 7 Sensor Health & Data Validation
        from core.data_quality.validation_engine import ValidationEngine
        self._validation_engine = ValidationEngine()
        # Phase 8 Fail-Safe & Safe Operation
        from core.safety.fail_safe import FailSafeManager
        from core.config.system_config import SystemConfig
        config = SystemConfig.load()
        self._config = config
        self._fail_safe = FailSafeManager(config)
        self._fail_safe.on_notification = self._on_fail_safe_notification
        
        # Phase 9 Communication Diagnostics
        from core.diagnostics.communication_monitor import CommunicationMonitor
        self.comm_monitor = CommunicationMonitor()
        
        # Phase 10 Auto Recovery (Reliability)
        self._auto_recovery = SelfDiagnosticsEngine(self.comm_monitor, config)
        
        # Phase 11 Historical Playback State
        self._playback_mode = False
        self._playback_time_iso = None
        self._playback_speed = 1
        
        # Phase 11.1 Scenario Manager
        from simulation.models.scenario_manager import ScenarioManager
        self._scenario_manager = ScenarioManager()
        
        # Register core GUI modules
        self.comm_monitor.register_module("HMI Core", interval=config.scan_interval)
        self.comm_monitor.register_module("Tag Database", interval=config.scan_interval)
        self.comm_monitor.register_module("Alarm Manager", interval=config.scan_interval)
        self.comm_monitor.register_module("AI Engine", interval=config.scan_interval)
        self.comm_monitor.register_module("Historian", interval=config.historian_flush_interval)
        self.comm_monitor.register_module("Digital Twin", interval=config.scan_interval)
        self.comm_monitor.register_module("Sensor Manager", interval=config.scan_interval)
        
        # Phase 5.5.4 Operational Intelligence KPI Engine
        from analytics.kpi.kpi_engine import KPIEngine
        self._kpi_engine = KPIEngine()
        
        # Phase 5.5.5 Adaptive AI & Model Lifecycle Management
        from analytics.ai.lifecycle.lifecycle_engine import LifecycleEngine
        self._lifecycle_engine = LifecycleEngine()
        self._lifecycle_engine.initialize_defaults()
        
        # Phase 5.5.6 Unified AI Decision Support
        from analytics.decision_support.decision_engine import DecisionEngine
        self._decision_engine = DecisionEngine()
        
        # Phase 5.5.7 What-If Scenario Analysis
        from analytics.simulation.scenario_engine import ScenarioEngine
        from analytics.simulation.impact_estimator import ImpactEstimator
        self._scenario_engine = ScenarioEngine()
        self._impact_estimator = ImpactEstimator()
        
        # Phase 10.6 AI Operator Assistant
        from analytics.ai.operator_assistant import AIOperatorAssistant
        self._ai_operator = AIOperatorAssistant()
        
        # Phase 10.7 AI Explainability Engine
        from analytics.ai.explainability.explainability_engine import HeuristicExplainer
        self._explainer_engine = HeuristicExplainer()
        
        # Phase 10.8 Predictive Maintenance Center Engine
        from analytics.ai.maintenance_engine import PredictiveMaintenanceCenterEngine
        self._pmc_engine = PredictiveMaintenanceCenterEngine()
        
        self._simulation_mode = False

        self._splash.update_progress(80, "Constructing User Interface...")
        
        # Build the GUI
        self._root.title("Dikili Geothermal SCADA  |  Industrial Control System")
        self._root.configure(bg=BG_PRIMARY)
        self._root.minsize(1280, 800)
        
        self._apply_ttk_style()

        try:
            self._root.state("zoomed")
        except tk.TclError:
            self._root.geometry("1600x900")
            
        self._splash.update_progress(100, "System Ready.")
        self._splash.close()
            
    def _apply_ttk_style(self):
        """Initialise base visual styles and custom themes."""
        # --- NEW GLOBAL THEME IMPORT ---
        from gui.theme import setup_theme
        setup_theme(self._root)
        # -------------------------------
        self._root.configure(bg=BG_PRIMARY)
        style = ttk.Style(self._root)
        style.theme_use("clam")
        
        # Configure Treeview colors
        style.configure(
            "Treeview",
            background=BG_SECONDARY,
            foreground=TEXT_PRIMARY,
            fieldbackground=BG_SECONDARY,
            borderwidth=0,
            font=("Segoe UI", 11),
            rowheight=35
        )
        
        # Configure Treeview header colors
        style.configure(
            "Treeview.Heading",
            background=BG_HEADER,
            foreground=TEXT_PRIMARY,
            borderwidth=1,
            relief="flat",
            font=FONT_LABEL_SM
        )
        
        # Configure selection color
        style.map("Treeview", background=[("selected", "#374151")], foreground=[("selected", "#60a5fa")])

        self._build_ui()
        self._root._handle_expand_chart = self._handle_expand_chart
        self._session_id = "OP-9021"
        self._logged_in_user = "Operator"
        self._root.withdraw()
        self._root.bind_all("<Any-KeyPress>", self._reset_activity_timer)
        self._root.bind_all("<Any-ButtonPress>", self._reset_activity_timer)
        self._root.after(100, self._show_login_screen)
        self._root.protocol("WM_DELETE_WINDOW", self._on_close_app)



    def _build_ui(self):
        # 1. Header (Top)
        self._build_header()

        # 2. Main Body (Sidebar + Content Area)
        self._paned_window = ttk.PanedWindow(self._root, orient=tk.HORIZONTAL)
        self._paned_window.pack(fill="both", expand=True)

        # -- Sidebar --
        sidebar_width = getattr(self._config.workspace, "sidebar_width", 280)
        sidebar = tk.Frame(self._paned_window, bg=BG_SECONDARY, width=sidebar_width, highlightbackground=BORDER, highlightthickness=1)
        sidebar.pack_propagate(False)
        self._paned_window.add(sidebar, weight=0)

        # Bottom Controls (pack first so they stick to the bottom)
        bottom_frame = tk.Frame(sidebar, bg=BG_SECONDARY)
        bottom_frame.pack(side="bottom", fill="x", pady=15, padx=15)

        # Language Switcher
        lang_frame = tk.Frame(bottom_frame, bg=BG_SECONDARY)
        lang_frame.pack(side="bottom", fill="x", pady=5)
        tk.Label(lang_frame, text="🇬🇧 EN / 🇹🇷 TR", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_LABEL_SM).pack(side="left")
        from gui.widgets import ToggleSwitch, ThemeToggle
        is_tr = (CURRENT_LANG == "tr")
        ToggleSwitch(lang_frame, is_on=is_tr, command=self._toggle_language, width=36, height=18).pack(side="right")

        # Theme Switcher (premium sun/moon toggle)
        theme_frame = tk.Frame(bottom_frame, bg=BG_SECONDARY)
        theme_frame.pack(side="bottom", fill="x", pady=5)
        from gui.theme import CURRENT_MODE
        is_dark = (CURRENT_MODE == "dark")
        ThemeToggle(theme_frame, is_dark=is_dark, command=self._toggle_theme).pack(side="right")

        # Navigation Container
        nav_frame = tk.Frame(sidebar, bg=BG_SECONDARY)
        nav_frame.pack(side="top", fill="both", expand=True, padx=15, pady=15)

        tk.Label(nav_frame, text="WORKSPACE", bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=("Segoe UI", 10, "bold")).pack(pady=(0, 5), anchor="w")

        # Search Bar
        search_frame = tk.Frame(nav_frame, bg=BG_SECONDARY)
        search_frame.pack(fill="x", pady=(0, 10))
        tk.Label(search_frame, text="🔍", bg=BG_SECONDARY, fg=TEXT_MUTED).pack(side="left")
        self._nav_search_var = tk.StringVar()
        self._nav_search_var.trace_add("write", self._on_nav_search)
        search_entry = ttk.Entry(search_frame, textvariable=self._nav_search_var, font=FONT_LABEL_SM)
        search_entry.pack(side="left", fill="x", expand=True, padx=(5, 0))

        self._nav_tree = ttk.Treeview(nav_frame, show="tree", selectmode="browse", height=20)
        self._nav_tree.pack(fill="both", expand=True)
        self._nav_tree.bind("<<TreeviewSelect>>", self._on_nav_tree_select)

        self.nav_buttons = {} # Kept for backward compatibility if plugins reference it
        self._current_panel = None
        self._panels = {}

        # Content Area
        self._content_area = tk.Frame(self._paned_window, bg=BG_PRIMARY)
        self._paned_window.add(self._content_area, weight=1)
        
        # Track PanedWindow resizing
        self._paned_window.bind("<ButtonRelease-1>", self._save_workspace_config)

        # Initialize HMI Panels
        from gui.historical_playback_panel import HistoricalPlaybackPanel
        from gui.mission_control_panel import MissionControlPanel
        from hmi.overview.overview_panel import OverviewPanel
        from hmi.operator_dashboard.dashboard import OperatorDashboard
        from hmi.trend_workspace.trend_panel import TrendWorkspace
        from hmi.alarm_center.alarm_manager_ui import AlarmCenterPanel
        from hmi.event_timeline.event_viewer import EventViewerPanel
        from hmi.diagnostics.diagnostics_panel import DiagnosticsPanel
        from gui.explainability_panel import ExplainabilityPanel
        from gui.rul_panel import RULPanel
        from gui.optimization_panel import OptimizationPanel
        from gui.anomaly_panel import AnomalyPanel
        from hmi.system_health.fail_safe_panel import FailSafePanel

        # Operations
        from gui.scenario_manager_panel import ScenarioManagerPanel
        from gui.reporting_center_panel import ReportingCenterPanel
        from gui.configuration_center_panel import ConfigurationCenterPanel
        
        self._panel_factories = {}
        self._panel_factories["config_center"] = lambda: ConfigurationCenterPanel(self._content_area)
        
        self._panel_factories["reporting_center"] = lambda: ReportingCenterPanel(
            self._content_area,
            self._enterprise_report_generator,
            on_generate_cb=self._on_generate_enterprise_report
        )
        self._panel_factories["scenario_manager"] = lambda: ScenarioManagerPanel(
            self._content_area, 
            self._scenario_manager,
            on_scenario_event_cb=self._on_scenario_event
        )
        self._panel_factories["playback"] = lambda: HistoricalPlaybackPanel(
            self._content_area, 
            self._historian,
            on_play_cb=self._handle_playback_play,
            on_stop_cb=self._handle_playback_stop,
            on_seek_cb=self._handle_playback_seek
        )
        self._panel_factories["mission_control"] = lambda: MissionControlPanel(self._content_area)
        def _create_overview():
            panel = OverviewPanel(self._content_area, well_ids=self._well_ids, on_equip_click=self._handle_equip_click)
            panel.on_sim_toggle_cb = self._handle_sim_mode_toggle
            return panel
        self._panel_factories["overview"] = _create_overview
        self._panel_factories["dashboard"] = lambda: OperatorDashboard(self._content_area)
        self._panel_factories["trends"] = lambda: TrendWorkspace(self._content_area, well_ids=self._well_ids, historian=self._historian)
        self._panel_factories["alarms"] = lambda: AlarmCenterPanel(self._content_area, alarm_manager=self._alarms, on_navigate=self.navigate_to_equipment, on_explain_cb=self.on_explain_requested)
        def _create_events():
            panel = EventViewerPanel(self._content_area)
            self._ai_event_log = panel
            return panel
        self._panel_factories["events"] = _create_events
        self._panel_factories["diagnostics"] = lambda: DiagnosticsPanel(self._content_area)
        self._panel_factories["fail_safe"] = lambda: FailSafePanel(self._content_area, self._fail_safe)
        
        from hmi.diagnostics.communication_panel import CommunicationPanel
        self._panel_factories["communication"] = lambda: CommunicationPanel(self._content_area, self.comm_monitor)
        
        from hmi.system_health.health_panel import HealthPanel
        import time
        self._panel_factories["health"] = lambda: HealthPanel(self._content_area, time.time(), self._historian, self._alarms)
        
        # Keep XAI Panel for AI Insights
        from gui.ai_explainability_panel import AIExplainabilityPanel
        self._panel_factories["xai"] = lambda: AIExplainabilityPanel(self._content_area)
        from gui.maintenance_center_panel import PredictiveMaintenanceCenterPanel
        self._panel_factories["rul"] = lambda: PredictiveMaintenanceCenterPanel(self._content_area)
        self._panel_factories["opt"] = lambda: OptimizationPanel(self._content_area)
        self._panel_factories["anomaly"] = lambda: AnomalyPanel(self._content_area)
        
        # Reliability Dashboard
        self._panel_factories["reliability"] = lambda: ReliabilityDashboard(
            self._content_area, 
            self._validation_engine, 
            self.comm_monitor, 
            self._fail_safe, 
            self._auto_recovery
        )
        
        # Executive Dashboard
        from gui.kpi_dashboard import KPIDashboard
        self._panel_factories["kpi"] = lambda: KPIDashboard(self._content_area)
        
        # Phase 5.5.5 Adaptive AI Lifecycle Dashboard
        from gui.ai_lifecycle_dashboard import AILifecycleDashboard
        self._panel_factories["lifecycle"] = lambda: AILifecycleDashboard(self._content_area)
        
        # Phase 5.5.6 Decision Support Panel
        from gui.decision_support_panel import DecisionSupportPanel
        self._panel_factories["dss"] = lambda: DecisionSupportPanel(self._content_area, on_navigate=self.navigate_to_equipment)
        
        # Phase 5.5.7 What-If Simulation Panel
        from gui.simulation_panel import SimulationPanel
        self._panel_factories["simulation"] = lambda: SimulationPanel(self._content_area, on_simulate_cb=self._handle_simulation)

        # AI Prediction History
        self._panel_factories["ai_history"] = lambda: PredictionHistoryPanel(self._content_area, self._history_logger)
        
        # AI Decision Timeline
        self._panel_factories["ai_timeline"] = lambda: AIDecisionTimelinePanel(self._content_area)
        
        # AI Model Information
        self._panel_factories["ai_info"] = lambda: AIModelInfoPanel(self._content_area)
        
        # AI Dataset Information
        self._panel_factories["ai_dataset"] = lambda: AIDatasetPanel(self._content_area)
        
        # Phase 10.6 AI Operator Assistant
        from gui.ai_operator_panel import AIOperatorPanel
        self._panel_factories["ai_operator"] = lambda: AIOperatorPanel(self._content_area)

        # The AI Event Log is assigned when the "events" panel is instantiated via lazy loading.
        # It defaults to None until the panel is first shown.
        self._ai_event_log = self._panels.get("events")
        # Populate Treeview
        self._nav_tree.insert("", "end", "operations", text="🛠️ " + tr("Operations"), open=True)
        self._nav_tree.insert("operations", "end", "mission_control", text="  " + tr("Mission Control"))
        self._nav_tree.insert("operations", "end", "reporting_center", text="  " + tr("Reporting Center"))
        self._nav_tree.insert("operations", "end", "scenario_manager", text="  " + tr("Scenario Manager"))
        self._nav_tree.insert("operations", "end", "playback", text="  " + tr("Historical Playback"))
        self._nav_tree.insert("operations", "end", "overview", text="  " + tr("Process Overview"))
        self._nav_tree.insert("operations", "end", "dashboard", text="  " + tr("Operator Dashboard"))
        self._nav_tree.insert("operations", "end", "trends", text="  " + tr("Trend Workspace"))
        self._nav_tree.insert("operations", "end", "alarms", text="  " + tr("Alarm Center"))
        self._nav_tree.insert("operations", "end", "events", text="  " + tr("Event Timeline"))
        
        self._nav_tree.insert("", "end", "engineering", text="⚙️ " + tr("Engineering"), open=True)
        self._nav_tree.insert("engineering", "end", "config_center", text="  " + tr("Configuration Center"))
        
        self._nav_tree.insert("", "end", "ai_analytics", text="🧠 " + tr("AI & Analytics"), open=True)
        self._nav_tree.insert("ai_analytics", "end", "ai_operator", text="  " + tr("AI Operator Assistant"))
        self._nav_tree.insert("ai_analytics", "end", "kpi", text="  " + tr("Executive Dashboard"))
        self._nav_tree.insert("ai_analytics", "end", "dss", text="  " + tr("Decision Support"))
        self._nav_tree.insert("ai_analytics", "end", "simulation", text="  " + tr("What-If Simulation"))
        self._nav_tree.insert("ai_analytics", "end", "ai_history", text="  " + tr("Prediction History"))
        self._nav_tree.insert("ai_analytics", "end", "ai_timeline", text="  " + tr("Decision Timeline"))
        self._nav_tree.insert("ai_analytics", "end", "xai", text="  " + tr("Explainable AI"))
        self._nav_tree.insert("ai_analytics", "end", "rul", text="  " + tr("Predictive Maintenance"))
        self._nav_tree.insert("ai_analytics", "end", "opt", text="  " + tr("Process Optimization"))
        self._nav_tree.insert("ai_analytics", "end", "anomaly", text="  " + tr("Anomaly Detection"))
        self._nav_tree.insert("ai_analytics", "end", "lifecycle", text="  " + tr("AI Lifecycle"))
        self._nav_tree.insert("ai_analytics", "end", "ai_info", text="  " + tr("AI Model Information"))
        self._nav_tree.insert("ai_analytics", "end", "ai_dataset", text="  " + tr("Dataset & Data Quality"))
        
        self._nav_tree.insert("", "end", "diagnostics_group", text="🛡️ " + tr("Diagnostics & Safety"), open=True)
        self._nav_tree.insert("diagnostics_group", "end", "health", text="  " + tr("System Health"))
        self._nav_tree.insert("diagnostics_group", "end", "diagnostics", text="  " + tr("System Diagnostics"))
        self._nav_tree.insert("diagnostics_group", "end", "fail_safe", text="  " + tr("Fail-Safe Manager"))
        self._nav_tree.insert("diagnostics_group", "end", "communication", text="  " + tr("Network & Comms"))
        self._nav_tree.insert("diagnostics_group", "end", "reliability", text="  " + tr("System Reliability"))
        
        # Save all original items for searching
        self._nav_items = []
        for parent in self._nav_tree.get_children(""):
            self._nav_items.append((parent, "", self._nav_tree.item(parent, "text")))
            for child in self._nav_tree.get_children(parent):
                self._nav_items.append((child, parent, self._nav_tree.item(child, "text")))

        # Select default
        last_panel = getattr(self._config.workspace, "last_panel", "mission_control")
        if last_panel not in self._panels:
            last_panel = "mission_control"
        self._switch_panel(last_panel)
        
    def on_explain_requested(self, equipment_id: str):
        """Called by UI components (like Alarm Panel) to trigger an AI Explanation."""
        # Calculate explanation using the latest engineered features
        if not hasattr(self, "_last_engineered_data") or not hasattr(self, "_last_ai_result"):
            return
            
        ai_result = self._last_ai_result
        features = self._last_engineered_data
        
        # Build explanation
        explanation = self._explainer_engine.generate_explanation(equipment_id, features, ai_result)
        
        risk = ai_result.get("Pump Failure Probability (%)", 0.0)
        conf = ai_result.get("Prediction Confidence (%)", 0.0)
        
        if "xai" in self._panels:
        
            self._panels["xai"].update_explanation(equipment_id, risk, conf, explanation)
        self._switch_panel("xai")
        
    def _handle_simulation(self, live_data: dict, overrides: dict):
        """Callback from SimulationPanel to run what-if scenarios."""
        sim_ai = self._scenario_engine.run_simulation(live_data, overrides)
        impact = self._impact_estimator.estimate_impact(
            self._panels["simulation"].live_ai if "simulation" in self._panels else {}, 
            sim_ai
        )
        
        if self._simulation_mode:
            import copy
            sim_facility = copy.deepcopy(self._facility)
            
            # Apply overrides to the mocked twin
            flow = overrides.get("Flow Rate (m3/h)", live_data.get("Flow Rate (m3/h)", 100))
            if "GW-01" in sim_facility.equipment:
                sim_facility.equipment["GW-01"].sensors["Flow Rate"] = flow
            if "P-101" in sim_facility.equipment:
                sim_facility.equipment["P-101"].sensors["Flow Rate"] = flow
                sim_facility.equipment["P-101"].status = sim_ai.get("Plant Status", "NORMAL")
                sim_facility.equipment["P-101"].failure_risk = sim_ai.get("Pump Failure Probability (%)", 0.0)
                sim_facility.equipment["P-101"].rul_hours = sim_ai.get("Remaining Useful Life (Hours)", 10000.0)
                sim_facility.equipment["P-101"].health_score = sim_ai.get("Equipment Health (%)", 100.0)
                sim_facility.equipment["P-101"].evaluate_status()
                
            if "overview" in self._panels:
                
                self._panels["overview"].update_from_twin(sim_facility)
            
        return sim_ai, impact
        
    def _handle_sim_mode_toggle(self, is_sim: bool):
        """Callback when the simulation mode toggle is switched in the Overview."""
        self._simulation_mode = is_sim
        if is_sim:
            # Re-evaluate with current overrides to populate twin instantly
            if "simulation" in self._panels:
                self._panels["simulation"]._run_simulation()
            
            from gui.window_manager import WindowManager
            if WindowManager.focus_if_exists("sim_mode_popup"):
                return
            
            # Premium Custom Popup
            popup = tk.Toplevel(self._root)
            WindowManager.register("sim_mode_popup", popup)
            popup.title(tr("Simulation Mode"))
            popup.configure(bg=BG_SECONDARY)
            popup.resizable(False, False)
            popup.transient(self._root)
            # Remove grab_set() so user can interact with the rest of the UI (non-blocking)
            
            # Content
            tk.Label(popup, text="⚠️", bg=BG_SECONDARY, fg="#3b82f6", font=("Segoe UI", 32)).pack(pady=(15, 5))
            msg = tr("Digital Twin is now showing SIMULATED values.\nLive plant data is still being recorded in the background.")
            tk.Label(popup, text=msg, bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_LABEL_SM, justify="center").pack(pady=5, padx=20)
            
            tk.Button(popup, text=tr("Acknowledge"), bg="#374151", fg="white", font=FONT_MONO_MD, 
                      relief="flat", cursor="hand2", command=popup.destroy, width=15).pack(pady=(10, 20))
                      
            # Center the popup automatically based on its content size
            popup.update_idletasks()
            w = popup.winfo_reqwidth()
            h = popup.winfo_reqheight()
            x = self._root.winfo_x() + (self._root.winfo_width() - w) // 2
            y = self._root.winfo_y() + (self._root.winfo_height() - h) // 2
            popup.geometry(f"{w}x{h}+{x}+{y}")
        else:
            self._facility.evaluate_all() # Reset colors
            if "overview" in self._panels:
                self._panels["overview"].update_from_twin(self._facility)

    def _on_nav_search(self, *args):
        query = self._nav_search_var.get().lower()
        # Detach all children
        for parent in ["operations", "ai_analytics", "diagnostics_group"]:
            for child in self._nav_tree.get_children(parent):
                self._nav_tree.detach(child)
        
        # Re-attach matching children
        for item, parent, text in self._nav_items:
            if parent: # Is a child node
                if query in text.lower() or not query:
                    self._nav_tree.move(item, parent, "end")
                    self._nav_tree.item(parent, open=True)

    def _on_nav_tree_select(self, event):
        sel = self._nav_tree.selection()
        if sel:
            item_id = sel[0]
            if item_id in self._panels or item_id in getattr(self, '_panel_factories', {}):
                self._switch_panel(item_id)

    def _save_workspace_config(self, event=None):
        if hasattr(self, '_paned_window'):
            try:
                # Calculate width based on sash position
                w = self._paned_window.sashpos(0)
                if w > 50:
                    self._config.workspace.sidebar_width = w
            except tk.TclError:
                pass

    def _switch_panel(self, key):
        if key not in self._panels and key not in getattr(self, '_panel_factories', {}):
            return
            
        is_new = False
        if key not in self._panels and key in getattr(self, '_panel_factories', {}):
            self._panels[key] = self._panel_factories[key]()
            is_new = True
            
        if key not in self._panels:
            return
            
        if self._current_panel:
            self._current_panel.pack_forget()

        self._current_panel = self._panels[key]
        self._current_panel.pack(fill="both", expand=True)
        
        if is_new and hasattr(self, '_last_tick_data'):
            self._force_panel_update(key)
            
    def _force_panel_update(self, key):
        if not hasattr(self, '_last_tick_data'): return
        data = self._last_tick_data
        panel = self._panels.get(key)
        if not panel: return
        
        try:
            import time
            if key == "overview":
                panel.update_from_twin(self._facility)
            elif key == "dashboard":
                highest_risk_eq = "P-101" if data["ai_result"]["Pump Failure Probability (%)"] > 40 else "None"
                crit_alarm = self._alarms.active_alarms[0].description if self._alarms.active_alarms else "None"
                panel.update_dashboard(
                    status=data["ai_result"]["Plant Status"],
                    health=data["health_indexes"].get("Overall Plant Health", 100.0),
                    highest_risk_eq=highest_risk_eq,
                    critical_alarm=crit_alarm,
                    power=self._hx_power,
                    energy=self._hx_power * ((time.time() - self._start_time) / 3600)
                )
            elif key == "trends" or key == "trend_detail":
                panel.update_data(data["readings"], data["reports"], ai_result=data["ai_result"], rul_results=data["rul_results"], health_indexes=data["health_indexes"])
            elif key == "alarms":
                panel.update_alarms()
            elif key == "reliability":
                panel.update_dashboard()
            elif key == "lifecycle":
                panel.update_dashboard(self._lifecycle_engine.get_dashboard_summary())
            elif key == "ai_operator" and data.get("op_assessment"):
                panel.update_dashboard(data["op_assessment"])
            elif key == "rul":
                panel.update_dashboard(data["pmc_profiles"])
            elif key == "mission_control":
                panel.update_dashboard(data["mc_snap"])
            elif key == "xai":
                explanation = self._explainer_engine.generate_explanation("GLOBAL", data.get("engineered_data", {}), data["ai_result"])
                panel.update_explanation(
                    target_id="GLOBAL",
                    risk=data["ai_result"]["Pump Failure Probability (%)"],
                    conf=data["ai_result"]["Prediction Confidence (%)"],
                    explanation=explanation
                )
            elif key == "opt":
                panel.update_dashboard(data["opt_result"])
                panel.update_history_graph(self._opt_engine.history)
            elif key == "anomaly":
                panel.update_anomaly(data["anomaly_result"])
                panel.update_history_graph(self._anomaly_engine.history.get_score_trend())
            elif key == "kpi":
                panel.update_dashboard(data["kpis"], self._kpi_engine.history)
            elif key == "dss":
                panel.update_dashboard(data["dss_assessments"], self._decision_engine.unified_recommendations)
            elif key == "simulation":
                panel.set_live_state(data["live_data"], data["ai_result"])
            elif key == "scenario_manager":
                panel.update_dashboard()
        except Exception as e:
            import traceback
            print(f"Error forcing update for {key}: {e}")
            traceback.print_exc()
        
        # Update tree selection if called externally
        try:
            current_sel = self._nav_tree.selection()
            if not current_sel or current_sel[0] != key:
                self._nav_tree.selection_set(key)
                self._nav_tree.see(key)
        except tk.TclError:
            pass
            
        self._config.workspace.last_panel = key

    def _toggle_theme(self, is_dark: bool):
        from gui.theme import set_theme_preference
        new_mode = "dark" if is_dark else "light"
        set_theme_preference(new_mode)
        self._restart_app()

    def _toggle_language(self, is_tr: bool):
        new_lang = "tr" if is_tr else "en"
        set_locale_preference(new_lang)
        self._restart_app()

    def _restart_app(self):
        import sys, os, subprocess
        subprocess.Popen([sys.executable, "-m", "gui.app"])
        self._root.quit()

    def _on_fail_safe_notification(self, desc: str, mode):
        from core.safety.fail_safe import SafeMode
        lvl = "CRIT" if mode == SafeMode.CRITICAL else ("WARN" if mode == SafeMode.WARNING else "INFO")
        if "events" in self._panels:
            if "events" in self._panels:
                self._panels["events"].add_event(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), lvl, desc)

    # ── Historical Playback Callbacks ──────────────────────────────────────
    def _handle_playback_play(self, current_iso: str, speed: int):
        self._playback_mode = True
        self._playback_time_iso = current_iso
        self._playback_speed = speed

    def _handle_playback_stop(self, pause_only: bool):
        if not pause_only:
            self._playback_mode = False
        else:
            # Just pause the progression, but remain in mode so we see the frozen frame
            self._playback_speed = 0

    def _handle_playback_seek(self, current_iso: str):
        self._playback_mode = True
        self._playback_time_iso = current_iso
        self._playback_speed = 0 # Paused on seek
        
    def _on_scenario_event(self, scenario, event_type: str):
        lvl = "WARN" if scenario.severity in ["HIGH", "CRITICAL"] else "INFO"
        if event_type == "ACTIVATED":
            msg = f"Scenario Activated: {scenario.name} (Severity: {scenario.severity})"
            if scenario.name == "Emergency Shutdown":
                self._alarms.raise_alarm("SCENARIO_ESD", "SYS", "EMERGENCY SHUTDOWN TRIGGERED VIA SCENARIO MANAGER", AlarmPriority.CRITICAL)
        else:
            msg = f"Scenario Stopped: {scenario.name}"
            
        if "events" in self._panels:
            if "events" in self._panels:
                self._panels["events"].add_event(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), lvl, msg)
            
        if not getattr(self, "_playback_mode", False):
            # Log to historian event tracker if it had one, or just add to mission control
            pass
            
    def _on_generate_enterprise_report(self):
        # Aggregate global plant state to build the reporting data structure
        ai_res = getattr(self, "_last_ai_result", {})
        health = getattr(self, "_last_health_indexes", {})
        maint = getattr(self, "_last_maint_rec", {})
        
        # Pull latest readings
        if hasattr(self, "_provider"):
            readings = self._provider.read_all()
        else:
            readings = []
            
        avg_temp = sum(r.temperature_c for r in readings) / max(1, len(readings))
        avg_pres = sum(r.pressure_bar for r in readings) / max(1, len(readings))
        total_flow = sum(r.flow_m3h for r in readings)
        
        hx_eff = getattr(self, "_hx_eff", 85.0)
        dh_flow = getattr(self, "_dh_flow", total_flow * 0.9)
        
        return {
            "scenario": self._scenario_manager.active_scenario.name if self._scenario_manager.active_scenario else "NORMAL",
            "overview": {
                "Overall Plant Health": f"{health.get('Overall Plant Health', 100.0):.1f}%",
                "Plant Status": ai_res.get("Plant Status", "NORMAL"),
                "Active Critical Alarms": self._alarms.summary().get("critical", False),
                "Total Flow": f"{total_flow:.1f} m³/h"
            },
            "production": {
                "Average Temperature": f"{avg_temp:.1f} °C",
                "Average Pressure": f"{avg_pres:.1f} bar",
                "Total Production Flow": f"{total_flow:.1f} m³/h",
                "Wells Online": len([r for r in readings if r.flow_m3h > 10])
            },
            "heating": {
                "District Heating Flow": f"{dh_flow:.1f} m³/h",
                "Heat Exchanger Efficiency": f"{hx_eff:.1f}%"
            },
            "energy": {
                "Estimated Power": f"{(total_flow * 4.186 * 15.0 / 3600 / 1000):.2f} MW"
            },
            "equipment": {
                w.well_id: ("Online" if w.is_healthy else "Offline") for w in readings
            },
            "alarms": [f"{tag}: {msg}" for tag, msg, prio, ts in self._alarms.get_active_alarms()],
            "maintenance": {
                "Priority": maint.get("Risk Level", "LOW"),
                "Recommended Action": ", ".join(maint.get("Recommended Actions", ["None"]))
            },
            "ai": {
                "Pump Failure Risk": f"{ai_res.get('Pump Failure Probability (%)', 0):.1f}%",
                "Prediction Confidence": f"{ai_res.get('Prediction Confidence (%)', 0):.1f}%"
            },
            "recommendations": ai_res.get("Operating Recommendations", ["Maintain current operation."])
        }

    def _build_header(self):
        hdr = tk.Frame(self._root, bg=BG_HEADER, height=40)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        title = tk.Label(hdr, text=f"  {tr('DIKILI GEOTHERMAL HMI')}",
                         bg=BG_HEADER, fg=TEXT_PRIMARY, font=FONT_HEADER_BAR, anchor="w")
        title.pack(side="left", padx=4)

        right_bar = tk.Frame(hdr, bg=BG_HEADER)
        right_bar.pack(side="right", padx=8)
        
        # Refresh Button
        btn_refresh = tk.Button(right_bar, text="⟳ " + tr("Refresh"), bg="#10b981", fg="white", font=FONT_LABEL_SM,
                                relief="flat", cursor="hand2", command=self._restart_app)
        btn_refresh.pack(side="right", padx=(10, 0), pady=4)
        
        btn_report = tk.Button(right_bar, text=tr("Generate AI Report"), bg="#2a4b6c", fg="white", font=FONT_LABEL_SM, 
                               relief="flat", cursor="hand2", command=self._generate_report_callback)
        btn_report.pack(side="right", padx=(10, 0), pady=4)

        self._status_led = StatusIndicator(right_bar, size=18)
        self._status_led.pack(side="right", padx=(4, 0))
        
        self._sys_health_lbl = tk.Label(right_bar, text="AI: ONLINE | HIST: ONLINE", bg=BG_HEADER, fg=TEXT_MUTED, font=FONT_LABEL_SM)
        self._sys_health_lbl.pack(side="right", padx=10)

        self._header_info = tk.Label(right_bar, text=tr("INITIALISING..."),
                                     bg=BG_HEADER, fg=TEXT_SECONDARY, font=FONT_MONO_SM)
        self._header_info.pack(side="right")

        # Logout Button
        self.btn_logout = tk.Button(right_bar, text=tr("Logout"), bg="#ef4444", fg="white", font=FONT_LABEL_SM,
                                    relief="flat", cursor="hand2", command=self._logout)
        self.btn_logout.pack(side="right", padx=(10, 0), pady=4)

        # Logged-in user indicator label
        self.lbl_user = tk.Label(right_bar, text="", bg=BG_HEADER, fg=TEXT_PRIMARY, font=FONT_LABEL_SM)
        self.lbl_user.pack(side="right", padx=(10, 0))

    def _handle_equip_click(self, equip_id: str, equip_type: str):
        from digital_twin.visualization.popups import EquipmentDetailPopup
        popup = EquipmentDetailPopup.get_or_create(self._root, equip_id, equip_type, app_context=self)
        eq = self._facility.get_equipment(equip_id)
        if eq:
            popup.update_from_twin(eq)

    def navigate_to_equipment(self, eq_id: str):
        """Global callback to focus on a specific equipment in the Digital Twin."""
        # 1. Switch to Overview Panel if not already there
        self._switch_panel("overview")
        # 2. Tell the diagram to focus it
        if "overview" in self._panels:
            self._panels["overview"].diagram.focus_equipment(eq_id)

    def _generate_report_callback(self):
        if not hasattr(self, '_last_ai_result'):
            import tkinter.messagebox as mb
            mb.showinfo("Report", "System is still initialising. Please wait for the first AI cycle.")
            return
            
        try:
            path = self._report_generator.generate_report(
                self._last_ai_result,
                self._last_health_indexes,
                self._last_maint_rec,
                self._alarms.summary()
            )
            if "events" in self._panels:
                self._panels["events"].add_event(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "INFO", f"Generated AI Report: {path}")
            import tkinter.messagebox as mb
            mb.showinfo("Report Generated", f"Daily Operational Report saved to:\n{path}")
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")

    # ── Data Loop ──────────────────────────────────────────────────────────

    def _tick(self):
        try:
            if not self._session_id:
                self._root.after(self._interval, self._tick)
                return
            self._cycle += 1

            if getattr(self, "_playback_mode", False):
                # Advance playback time
                from datetime import timedelta
                import dateutil.parser
                if self._playback_speed > 0 and self._playback_time_iso:
                    current = dateutil.parser.parse(self._playback_time_iso)
                    current += timedelta(milliseconds=self._interval * self._playback_speed)
                    self._playback_time_iso = current.isoformat()
                    if "playback" in self._panels:
                        if "playback" in self._panels:
                            self._panels["playback"].update_playback_time(self._playback_time_iso)
                
                # Fetch snapshot
                if self._playback_time_iso:
                    snap_data = self._historian.get_snapshot_at(self._playback_time_iso)
                    readings = []
                    for row in snap_data:
                        r = SensorReading(
                            well_id=row.get("well_id", ""),
                            temperature_c=row.get("temperature_c", 0.0),
                            pressure_bar=row.get("pressure_bar", 0.0),
                            flow_m3h=row.get("flow_m3h", 0.0),
                            is_healthy=bool(row.get("is_healthy", True))
                        )
                        readings.append(r)
                else:
                    readings = []
            else:
                self._scada.tick()  # Restore original SCADASystem tick
                readings = self._provider.read_all()
                
            # Apply Scenario Engine Modifiers
            if not getattr(self, "_playback_mode", False):
                readings = self._scenario_manager.apply_scenario_modifiers(readings, time.time())
                
            reports  = {r.well_id: self._detector.evaluate_from_reading(r) for r in readings}

            val_warnings, val_errors = self._validation_engine.validate_sensors(readings, time.time())
        
            # Report active sensor errors to Fail-Safe Manager
            for tag_id in self._validation_engine._sensors:
                diag = self._validation_engine._get_diag(tag_id)
                if diag.error_count > 0:
                    self._fail_safe.report_failure(tag_id, f"Sensor {tag_id} reported validation errors.")
                else:
                    self._fail_safe.report_recovery(tag_id)
                
            for w in val_warnings:
                if "events" in self._panels:
                    self._panels["events"].add_event(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "WARN", w)
            for e in val_errors:
                if "events" in self._panels:
                    self._panels["events"].add_event(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CRIT", e)
                if "RANGE" in e or "OFFLINE" in e:
                    self._alarms.raise_alarm(f"SENSOR_{self._cycle}", "SYS", e, AlarmPriority.HIGH)

            avg_temp = sum(r.temperature_c for r in readings) / len(readings)
            avg_pres = sum(r.pressure_bar  for r in readings) / len(readings)
            total_flow = sum(r.flow_m3h    for r in readings)
            max_risk = max(rpt.risk_score  for rpt in reports.values()) if reports else 0.0

            # Simulated HX / DH values
            self._hx_eff   = 82.0 + 6.0 * math.sin(time.time() / 600) + random.gauss(0, 0.3)
            self._hx_eff   = max(70.0, min(95.0, self._hx_eff))
            self._hx_power = total_flow * 4.186 * 15.0 / 3600 / 1000
            self._dh_flow  = total_flow * 0.92
            self._dh_dt    = 12.0 + 3.0 * math.sin(time.time() / 900) + random.gauss(0, 0.2)

            self._evaluate_alarms(readings, reports)
        except Exception as e:
            logger.error(f"Error in alarm evaluation: {e}", exc_info=True)
        try:
        
            # Update UI components
            self._update_header(max_risk)
        except Exception as e: 
            logger.error(f"Error updating header: {e}", exc_info=True)
        try:
        
            # Prepare raw SCADA sensor data for Digital Twin
            scada_data = {}
            # We consolidate reading averages for the single string layout
            scada_data["GW-01"] = {"Temperature": avg_temp, "Pressure": avg_pres, "Flow Rate": total_flow, "Operating Hours": 5400}
            scada_data["P-101"] = {"Flow Rate": total_flow, "Motor Current (A)": total_flow * 0.45, "Power (kW)": total_flow * 0.45 * 1.73, "Operating Hours": 2500}
            scada_data["PROD-PIPE"] = {"Flow Rate": total_flow, "Pressure Drop": avg_pres * 0.05}
            scada_data["SEP-01"] = {"Pressure": avg_pres * 0.85, "Brine Level": 65.0}
            scada_data["HX-101"] = {"Efficiency": self._hx_eff, "Thermal Power": self._hx_power}
            scada_data["P-201"] = {"Flow Rate": self._dh_flow, "Motor Current (A)": self._dh_flow * 0.35, "Power (kW)": self._dh_flow * 0.35 * 1.73, "Operating Hours": 1800}
            scada_data["DH-NET"] = {"Flow Rate": self._dh_flow, "Delta T": self._dh_dt}
            scada_data["RET-PIPE"] = {"Flow Rate": self._dh_flow * 0.98, "Temperature": avg_temp - self._dh_dt}
            scada_data["P-301"] = {"Flow Rate": self._dh_flow * 0.98, "Motor Current (A)": self._dh_flow * 0.40, "Power (kW)": self._dh_flow * 0.40 * 1.73, "Operating Hours": 2100}
            scada_data["RW-01"] = {"Flow Rate": self._dh_flow * 0.98, "Wellhead Pressure": 8.5}
        
            self._facility.update_from_scada(scada_data)
            reliability_manager.update_status("Digital Twin", SubsystemStatus.ONLINE)
        except Exception as e:
            reliability_manager.update_status("Digital Twin", SubsystemStatus.DEGRADED, event=str(e), severity="WARNING", recovery_action="Bypassing visual updates")
            logger.error(f"Error during SCADA tick: {e}")
            import traceback; traceback.print_exc()
        try:
            # ─── AI INTEGRATION ────────────────────────────────────────────────────
            # 1. Build live feature vector
            pump_running = 1 if total_flow > 10 else 0
            live_data = {
                "Temperature (°C)": avg_temp,
                "Pressure (bar)": avg_pres,
                "Flow Rate (m3/h)": total_flow,
                "Pump Speed (%)": 100.0 if pump_running else 0.0,
                "Pump Running (0/1)": pump_running,
                "Motor Current (A)": total_flow * 0.45 if pump_running else 0.0,
                "Motor Voltage (V)": 400.0,
                "Motor Power (kW)": (total_flow * 0.45 * 400.0 * 1.732 * 0.85 / 1000.0) if pump_running else 0.0,
                "Pump Operating Hours": 2500.0 + (self._cycle * self._interval / 3600000.0),
                "Heat Exchanger Inlet Temperature": avg_temp,
                "Heat Exchanger Outlet Temperature": avg_temp - (avg_temp * self._hx_eff / 100.0 * 0.2),
                "Heat Exchanger Efficiency": self._hx_eff,
                "District Heating Supply Temperature": avg_temp - 5.0,
                "District Heating Return Temperature": max(40.0, avg_temp - 5.0 - self._dh_dt),
                "Thermal Power (MW)": self._hx_power,
                "Pressure Drop": avg_pres * 0.1,
                "Daily Energy": self._hx_power * 24.0,
                "Outside Air Temperature": 15.0,
                "Plant Load": 70.0,
                "Alarm Count": len(self._alarms.active_alarms),
                "Health Score": 100.0 - max_risk,
                "Data Quality Score": self._validation_engine.global_quality_score,
            }

            # Validate AI Inputs before engineering
            ai_warnings, ai_errors = self._validation_engine.validate_ai_inputs(live_data)
            for e in ai_errors:
                if "events" in self._panels:
                    self._panels["events"].add_event(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CRIT", e)

            # 2. Engineer Features
            engineered_data = self._feature_engineer.process_row(live_data)

            # 3. Predict AI State
            from analytics.ai.random_forest.predictor import predict_plant_state
        
            # Check Fail-Safe before running AI
            if self._fail_safe.is_ai_allowed():
                ai_input = engineered_data.copy()
                ai_input.pop("Data Quality Score", None)
            
                # Async AI Worker
                if not hasattr(self, "_cached_ai_result"):
                    self._cached_ai_result = {
                        "Plant Status": "NORMAL", "Pump Failure Probability (%)": 0.0,
                        "Equipment Health (%)": 100.0, "Prediction Confidence (%)": 100.0
                    }
                if not hasattr(self, "_cached_shap_res"):
                    self._cached_shap_res = {"positive_factors": [], "negative_factors": [], "explanation_text": ""}

                if self._cycle % 10 == 0:
                    import threading
                    def _run_ai_async():
                        try:
                            res = predict_plant_state(ai_input, self._lifecycle_engine)
                            shap = self._explainer.explain_prediction("GLOBAL", engineered_data, res["Pump Failure Probability (%)"])
                            self._cached_ai_result = res
                            self._cached_shap_res = shap
                        except Exception as e:
                            import traceback
                            traceback.print_exc()
                            print(f"Async AI thread failed: {e}")
                            
                    threading.Thread(target=_run_ai_async, daemon=True).start()
                
                ai_result = self._cached_ai_result
            else:
                # Provide safe fallback when AI is disabled
                ai_result = {
                    "Plant Status": "SAFE_MODE",
                    "Pump Failure Probability (%)": 0.0,
                    "Equipment Health (%)": 0.0,
                    "Prediction Confidence (%)": 0.0
                }

            # 3.5 Evaluate AI Lifecycle
            self._lifecycle_engine.evaluate(live_data)
            if "lifecycle" in self._panels:
                self._panels["lifecycle"].update_dashboard(self._lifecycle_engine.get_dashboard_summary())

            # 4. Update Event Log and Alarms
            new_status = ai_result["Plant Status"]
            if new_status != self._last_ai_status:
                lvl = "CRIT" if new_status == "CRITICAL" else ("WARN" if new_status == "WARNING" else "INFO")
                if "events" in self._panels:
                    self._panels["events"].add_event(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), lvl, f"AI Status Shift: {new_status} (Conf: {ai_result['Prediction Confidence (%)']:.1f}%)")
                self._last_ai_status = new_status
            
            # Specific multiline log format requested for Phase 3.3
            log_msg = (
                f"AI Prediction: Pump {'RUNNING' if pump_running else 'STOPPED'}, "
                f"Risk: {ai_result['Pump Failure Probability (%)']:.0f}%, "
                f"Health: {ai_result['Equipment Health (%)']:.0f}%"
            )
            if self._cycle % 10 == 0 or ai_result["Pump Failure Probability (%)"] > 70:
                if "events" in self._panels:
                    self._panels["events"].add_event(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "INFO", log_msg)
            
            # Alarm Integration
            from scada.alarm_manager import AlarmCategory
            if ai_result["Pump Failure Probability (%)"] > 70.0:
                if "AI_PUMP_FAIL" not in self._alarms._active:
                    self._alarms.raise_alarm(
                        alarm_id="AI_PUMP_FAIL",
                        tag_id="AI_PRED",
                        description="AI predicted critical pump failure",
                        priority=AlarmPriority.HIGH,
                        category=AlarmCategory.PREDICTIVE_AI
                    )
            else:
                if "AI_PUMP_FAIL" in self._alarms._active:
                    self._alarms.clear_alarm("AI_PUMP_FAIL")
        
            # ───────────────────────────────────────────────────────────────────────
                
            # 6. SHAP Explanation & Advanced Analytics
            shap_res = getattr(self, "_cached_shap_res", {"positive_factors": [], "negative_factors": [], "explanation_text": ""})
                
            self._history_logger.log_prediction(ai_result, shap_res)
            
            # Phase 10.6 AI Operator Assistant Evaluation
            op_assessment = self._ai_operator.evaluate(readings, reports)
            op_assessment.plant_status = ai_result.get("Plant Status", "NORMAL")
            op_assessment.confidence_score = ai_result.get("Prediction Confidence (%)", 90.0)
            if "ai_operator" in self._panels:
                self._panels["ai_operator"].update_dashboard(op_assessment)
            
            # Cache latest for Explainability Engine
            self._last_engineered_data = engineered_data
            self._last_ai_result = ai_result
        
            # 6.5 AI Decision Explanation Timeline
            decision_event = DecisionAnalyzer.analyze_decision(engineered_data, ai_result)
            self._decision_timeline.log_decision(decision_event)
        
            # Phase 4: Health Index, Maintenance Recommendation, and Trend Analysis
            health_indexes = self._health_engine.calculate_indexes(live_data, ai_result)
            maint_rec = self._maintenance_engine.get_recommendations(ai_result, health_indexes, live_data, shap_res)
            
            # Phase 10.8 Predictive Maintenance Center
            pmc_profiles = self._pmc_engine.evaluate_plant_maintenance(readings, ai_result, health_indexes)
            if "rul" in self._panels:
                self._panels["rul"].update_dashboard(pmc_profiles)
            
            # Phase 10.9 Mission Control Dashboard
            mc_snap = {
                "plant_status": ai_result.get("Plant Status", "NORMAL"),
                "health": sum(p.health_score for p in pmc_profiles) / max(1, len(pmc_profiles)),
                "ai_conf": ai_result.get("Prediction Confidence (%)", 100.0),
                "op_mode": self._scenario_engine.current_scenario.name if hasattr(self._scenario_engine, 'current_scenario') else "NORMAL",
                "prod_flow": sum(r.flow_m3h for r in readings if "PW" in r.well_id),
                "heat_out": sum(r.temperature_c * r.flow_m3h * 0.00116 for r in readings if "PW" in r.well_id), # Rough MW est
                "energy_prod": ai_result.get("Energy Efficiency (%)", 0.0), # or placeholder
                "dh_demand": 50.0, # fallback
                "inj_flow": sum(r.flow_m3h for r in readings if "IW" in r.well_id),
                "risk_equip": max(pmc_profiles, key=lambda p: p.failure_probability).equipment_id if pmc_profiles else "None",
                "risk_level": max(pmc_profiles, key=lambda p: p.failure_probability).priority if pmc_profiles else "LOW",
                "maint_due": next((p.equipment_id for p in pmc_profiles if p.priority in ("CRITICAL", "HIGH")), "None"),
                "alarms": len(self._alarms.active_alarms),
                "incidents": len(self._alarms.active_alarms) # Simplified
            }
            if "mission_control" in self._panels:
                # Dashboard Refresh Optimization: Only update if changed
                if not hasattr(self, "_last_mc_snap") or self._last_mc_snap != mc_snap:
                    if "mission_control" in self._panels:
                        self._panels["mission_control"].update_dashboard(mc_snap)
                    self._last_mc_snap = mc_snap
        
            # 7. Update Digital Twin with AI logic
            ai_data = {}
        
            if "xai" in self._panels:
                pass # Do not automatically overwrite equipment explanation with global on every tick
        
            rul_results = {}
            for eq_id in ["GW-01", "P-101", "PROD-PIPE", "SEP-01", "HX-101", "P-201", "DH-NET", "RET-PIPE", "P-301", "RW-01"]:
                risk = ai_result["Pump Failure Probability (%)"] if "P-" in eq_id else (ai_result["Pump Failure Probability (%)"] * 0.4)
                health = health_indexes.get("Pump Health", 100.0) if "P-" in eq_id else health_indexes.get("Overall Plant Health", 100.0)
            
                rul_data = self._rul_engine.estimate_rul(eq_id, live_data, ai_result, health)
                rul_results[eq_id] = rul_data
            
                ai_data[eq_id] = {
                    "health": health,
                    "risk": risk,
                    "conf": ai_result["Prediction Confidence (%)"],
                    "recommendation": maint_rec.get("action", "Continue Monitoring") if "P-" in eq_id else "Normal operation",
                    "pos_factors": shap_res.get("positive_factors", []),
                    "neg_factors": shap_res.get("negative_factors", []),
                    "explanation_text": shap_res.get("explanation_text", "No explanation available."),
                    "rul_hours": rul_data["Remaining Useful Life (Hours)"],
                    "estimated_days": rul_data.get("Estimated Remaining Days", 0.0),
                    "rul_conf": rul_data["Confidence (%)"],
                    "degradation_rate": rul_data.get("Degradation Rate", 0.0),
                    "rul_trend": rul_data["Current Degradation"],
                    "maintenance_priority": rul_data.get("Maintenance Priority", "Unknown")
                }
            reliability_manager.update_status("AI Engine", SubsystemStatus.ONLINE)
        except Exception as e:
            reliability_manager.update_status("AI Engine", SubsystemStatus.OFFLINE, event=str(e), severity="ERROR", recovery_action="Bypassing AI recommendations")
            ai_result = {
                "Plant Status": "SAFE_MODE (AI OFFLINE)",
                "Pump Failure Probability (%)": 0.0,
                "Equipment Health (%)": 0.0,
                "Prediction Confidence (%)": 0.0
            }
            health_indexes = {"Overall Plant Health": 0.0}
            maint_rec = {"action": "None"}
            rul_results = {}
            logger.error(f"Error evaluating AI engine: {e}", exc_info=True)
        try:
        
            # Scenario Manager AI Modifiers
            if not getattr(self, "_playback_mode", False):
                ai_result = self._scenario_manager.apply_ai_modifiers(ai_result)

            # --- Phase 5.5.2 Optimization Engine ---
            opt_result = self._opt_engine.evaluate(live_data, ai_result)
            if "opt" in self._panels:
                self._panels["opt"].update_dashboard(opt_result)
            if "opt" in self._panels:
                self._panels["opt"].update_history_graph(self._opt_engine.history)
        
            opt_data_for_twin = {}
            for rec in opt_result.get("Recommendations", []):
                eq_id = rec.get("Equipment")
                if eq_id == "GW-01 System": eq_id = "GW-01"
                opt_data_for_twin[eq_id] = {
                    "efficiency": rec.get("Efficiency", 0.0),
                    "target_efficiency": rec.get("Target Efficiency", 0.0),
                    "suggestion": rec.get("Suggestion", ""),
                    "estimated_improvement": rec.get("Estimated Improvement", "")
                }
            self._facility.update_from_optimization(opt_data_for_twin)
            # ---------------------------------------
        
            # --- Phase 5.5.3 Anomaly Detection Engine ---
            anomaly_result = self._anomaly_engine.evaluate(live_data, ai_result)
            if "anomaly" in self._panels:
                self._panels["anomaly"].update_anomaly(anomaly_result)
            if "anomaly" in self._panels:
                self._panels["anomaly"].update_history_graph(self._anomaly_engine.history.get_score_trend())
            self._facility.update_from_anomaly(anomaly_result)
            # ---------------------------------------------
        
            # --- Phase 5.5.4 Operational Intelligence KPI Engine ---
            kpis = self._kpi_engine.evaluate(live_data, ai_result, health_indexes, maint_rec, rul_results, opt_result)
            if "kpi" in self._panels:
                self._panels["kpi"].update_dashboard(kpis, self._kpi_engine.history)
            self._facility.update_from_kpi(kpis)
            # ---------------------------------------------
        
            # --- Phase 5.5.6 Unified AI Decision Support ---
            dss_assessments = self._decision_engine.evaluate(ai_result, rul_results, health_indexes, anomaly_result, opt_result)
            if "dss" in self._panels:
                self._panels["dss"].update_dashboard(dss_assessments, self._decision_engine.unified_recommendations)
            self._facility.update_from_decision(dss_assessments)
            # ---------------------------------------------
        
            # Digital Twin Optimization: Only update physics/visuals every N ticks
            if self._cycle % 5 == 0:
                self._facility.evaluate_all()
        
            # Log to Historian
            if not getattr(self, "_playback_mode", False):
                for r in readings:
                    self._historian.log_sensor_reading(r.well_id, r.temperature_c, r.pressure_bar, r.flow_m3h, r.is_healthy)
                    eq_id = r.well_id
                    rul_data = rul_results.get(eq_id, {})
                    self._historian.log_ai_prediction(
                        eq_id, 
                        ai_result["Pump Failure Probability (%)"], 
                        ai_result["Plant Status"], 
                        reports[eq_id].risk_score if eq_id in reports else 0.0,
                        rul_data.get("Remaining Useful Life (Hours)", 0.0),
                        rul_data.get("Confidence (%)", 0.0)
                    )
        
            # 8. Refresh Visualizations from Twin
            if not self._simulation_mode:
                if "overview" in self._panels:
                    self._panels["overview"].update_from_twin(self._facility)
                    
                    # Update Overview Dashboard KPIs and AI Insights
                    overview_kpis = {
                        "Production": f"{total_flow:.1f} m³/h",
                        "Steam Flow": f"{total_flow * 0.15:.1f} t/h",
                        "Temperature": f"{avg_temp:.1f} °C",
                        "Pressure": f"{avg_pres:.1f} bar",
                        "Power": f"{self._hx_power:.1f} MW",
                        "Efficiency": f"{self._hx_eff:.1f} %",
                        "Energy": f"{self._hx_power * 24.0:.1f} MWh",
                        "Active Alarms": str(len(self._alarms.active_alarms)),
                        "AI Status": ai_result.get("Plant Status", "NORMAL")
                    }
                    
                    overview_ai_insights = {
                        "Overall AI Status": ai_result.get("Plant Status", "NORMAL"),
                        "Risk Score": f"{ai_result.get('Pump Failure Probability (%)', 0.0):.1f}",
                        "Confidence": f"{ai_result.get('Prediction Confidence (%)', 0.0):.1f}",
                        "Equipment Health": f"{ai_result.get('Equipment Health (%)', 100.0):.1f}",
                        "RUL": str(rul_results.get("P-101", {}).get("Remaining Useful Life (Hours)", 0.0)),
                        "Prediction": ai_result.get("Plant Status", "NORMAL"),
                        "Recommendation": maint_rec.get("action", "Monitor system normally.")
                    }
                    self._panels["overview"].update_dashboard_data(overview_kpis, overview_ai_insights)
            
            # Update simulation baseline
            if "simulation" in self._panels:
                self._panels["simulation"].set_live_state(live_data, ai_result)
            
            # Update Scenario Manager Timeline
            if "scenario_manager" in self._panels:
                if "scenario_manager" in self._panels:
                    self._panels["scenario_manager"].update_dashboard()
        
            from digital_twin.visualization.popups import EquipmentDetailPopup
            from gui.window_manager import WindowManager
        
            for win_id, popup in list(WindowManager._windows.items()):
                if isinstance(popup, EquipmentDetailPopup):
                    eq = self._facility.get_equipment(popup.equip_id)
                    if eq:
                        popup.update_from_twin(eq)
        
            self._last_ai_result = ai_result
            self._last_health_indexes = health_indexes
            self._last_maint_rec = maint_rec
            
            self._last_tick_data = {
                "readings": readings,
                "reports": reports,
                "ai_result": ai_result,
                "rul_results": rul_results,
                "health_indexes": health_indexes,
                "maint_rec": maint_rec,
                "scada_data": scada_data if 'scada_data' in locals() else {},
                "anomaly_result": anomaly_result if 'anomaly_result' in locals() else {},
                "opt_result": opt_result if 'opt_result' in locals() else {},
                "kpis": kpis if 'kpis' in locals() else {},
                "dss_assessments": dss_assessments if 'dss_assessments' in locals() else {},
                "live_data": live_data if 'live_data' in locals() else {},
                "engineered_data": engineered_data if 'engineered_data' in locals() else {},
                "shap_res": shap_res if 'shap_res' in locals() else {},
                "pmc_profiles": pmc_profiles if 'pmc_profiles' in locals() else [],
                "mc_snap": mc_snap if 'mc_snap' in locals() else {},
                "op_assessment": op_assessment if 'op_assessment' in locals() else None,
            }
        
            # 9. Update HMI Panels
            highest_risk_eq = "P-101" if ai_result["Pump Failure Probability (%)"] > 40 else "None"
            crit_alarm = self._alarms.active_alarms[0].description if self._alarms.active_alarms else "None"
        
            if "dashboard" in self._panels:
        
                self._panels["dashboard"].update_dashboard(
                status=ai_result["Plant Status"],
                health=health_indexes.get("Overall Plant Health", 100.0),
                highest_risk_eq=highest_risk_eq,
                critical_alarm=crit_alarm,
                power=self._hx_power,
                energy=self._hx_power * ((time.time() - self._start_time) / 3600)
            )
            if "trends" in self._panels:
                self._panels["trends"].update_data(readings, reports, ai_result=ai_result, rul_results=rul_results, health_indexes=health_indexes)
        
            if "trend_detail" in self._panels and self._current_panel == "trend_detail":
                if "trend_detail" in self._panels:
                    self._panels["trend_detail"].update_data(readings, reports, ai_result=ai_result, rul_results=rul_results, health_indexes=health_indexes)
            
            if "alarms" in self._panels:
            
                self._panels["alarms"].update_alarms()
        
            self._auto_recovery.evaluate()
            if "reliability" in self._panels:
                if "reliability" in self._panels:
                    self._panels["reliability"].update_dashboard()
        
            # Diagnostics
            twin_status = "SYNCED" if self._cycle > 0 else "OFFLINE"
            self._diag_service.update_status("SIM", "RUNNING")
            self._diag_service.update_status("DB", "ONLINE" if self._historian._conn else "ERROR")
        
            # 5. Evaluate remaining components (RUL, Anomaly)
        
            # 6. Update Fail-Safe Manager
            self._fail_safe.tick()
        
            # 7. Simulate network diagnostics for modules
            self._simulate_network_diagnostics()

            # Update Historian (approximate periodic write)
            if self._cycle % 30 == 0:
                for r in readings:
                    self._historian.log_sensor_reading(r.well_id, r.temperature_c, r.pressure_bar, r.flow_m3h, r.is_healthy)

        except Exception as e:
            logger.error(f"Error at end of tick cycle: {e}", exc_info=True)
        finally:
            # Schedule next tick regardless of exceptions to prevent UI freeze
            self._root.after(self._interval, self._tick)

    def _simulate_network_diagnostics(self):
        import random
        # Base synchronous modules
        for mod in ["HMI Core", "Tag Database", "Alarm Manager", "Digital Twin", "Sensor Manager"]:
            self.comm_monitor.record_heartbeat(mod, random.uniform(0.1, 2.5))
            
        # Simulate AI Engine (sometimes slower)
        if random.random() > 0.05:
            self.comm_monitor.record_heartbeat("AI Engine", random.uniform(5.0, 45.0))
        else:
            self.comm_monitor.record_error("AI Engine", "dropped")
            
        # Simulate Historian
        if self._cycle % 30 == 0:
            self.comm_monitor.record_heartbeat("Historian", random.uniform(15.0, 120.0))
            
        self.comm_monitor.evaluate_health()

    def _evaluate_alarms(self, readings: list, reports: dict):
        for r in readings:
            wid = r.well_id
            if r.temperature_c >= _T_HI_HI:
                self._alarms.raise_alarm(f"{wid}.TEMP.HIHI", wid, f"HIGH TEMP {wid} (HI-HI)", AlarmPriority.CRITICAL)
            elif r.temperature_c >= _T_HI:
                self._alarms.raise_alarm(f"{wid}.TEMP.HI", wid, f"HIGH TEMP {wid} (HI)", AlarmPriority.HIGH)
            else:
                self._alarms.clear_alarm(f"{wid}.TEMP.HIHI")
                self._alarms.clear_alarm(f"{wid}.TEMP.HI")

            # Basic logic to emit events for large state changes (for Event Log)
            rpt = reports.get(wid)
            if rpt and rpt.risk_score >= _RISK_CRIT:
                self._alarms.raise_alarm(f"{wid}.PUMP.RISK", wid, f"PUMP RISK {wid}", AlarmPriority.CRITICAL)
            else:
                self._alarms.clear_alarm(f"{wid}.PUMP.RISK")

    def _update_header(self, max_risk: float):
        now_str = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        elapsed = int(time.time() - self._start_time)
        up_str  = f"{elapsed // 3600:02d}:{(elapsed % 3600) // 60:02d}:{elapsed % 60:02d}"

        health = "CRITICAL" if max_risk >= _RISK_CRIT else ("WARNING" if max_risk >= _RISK_WARN else "GOOD")
        
        # Reliability Statuses
        ai_stat = reliability_manager.get_status("AI Engine").value
        hist_stat = reliability_manager.get_status("Historian").value
        dt_stat = reliability_manager.get_status("Digital Twin").value
        
        self._header_info.config(
            text=f"{now_str}  |  UP: {up_str}  |  OP: Admin  |  AI: {ai_stat}  |  HIST: {hist_stat}  |  TWIN: {dt_stat}  |  {health}  ",
            fg=status_color(health),
        )
        self._status_led.set_status(health)

    def _close_trend_detail(self):
        self._switch_panel("trends")
        if "trend_detail" in self._panels:
            if "trend_detail" in self._panels:
                self._panels["trend_detail"].pack_forget()
            if "trend_detail" in self._panels:
                self._panels["trend_detail"].destroy()
            del self._panels["trend_detail"]

    def _handle_expand_chart(self, chart_key: str, title: str):
        from hmi.trend_workspace.trend_detail_panel import TrendDetailPanel
        
        if "trend_detail" in self._panels:
            if "trend_detail" in self._panels:
                self._panels["trend_detail"].pack_forget()
            if "trend_detail" in self._panels:
                self._panels["trend_detail"].destroy()
            
        self._panels["trend_detail"] = TrendDetailPanel(
            self._content_area,
            chart_key=chart_key,
            title=title,
            historian=self._historian,
            well_ids=self._well_ids,
            on_close=self._close_trend_detail
        )
        
        # Pass live data so it doesn't have to wait for the next tick
        live_data_ref = self._panels["trends"].charts._data
        live_times_ref = self._panels["trends"].charts._times
        
        visibilities = {}
        for wid in self._well_ids:
            line = self._panels["trends"].charts._lines.get(chart_key, {}).get(wid)
            visibilities[wid] = line.get_visible() if line else True
            
        if "trend_detail" in self._panels:
            
            self._panels["trend_detail"].initialize_from_live(live_times_ref, live_data_ref, visibilities)
        
        self._switch_panel("trend_detail")

    def _update_kpis(self, avg_temp, avg_pres, total_flow, max_risk):
        self._kpis["temp"].set_value(avg_temp)
        self._kpis["pres"].set_value(avg_pres)
        self._kpis["flow"].set_value(total_flow)
        self._kpis["power"].set_value(self._hx_power)
        self._kpis["eff"].set_value(self._hx_eff)
        self._kpis["util"].set_value(100.0) # all 3 running
        self._kpis["energy"].set_value(self._hx_power * ((time.time() - self._start_time) / 3600))
        self._kpis["alarms"].set_value(len(self._alarms.active_alarms), color=CLR_CRITICAL if self._alarms.active_alarms else CLR_NORMAL)
        self._kpis["risk"].set_value(max_risk, color=CLR_CRITICAL if max_risk > _RISK_CRIT else CLR_NORMAL)

    def _update_pumps(self, readings: list):
        for r in readings:
            wid = r.well_id
            if r.flow_m3h < _Q_LO_LO:
                state, v_state = "FAULT", "CLOSED"
            elif r.flow_m3h < _Q_LO:
                state, v_state = "STARTING", "THROTTLED"
            else:
                state, v_state = "RUNNING", "OPEN"
                
            if wid in self._pumps:
                self._pumps[wid].set_state(state, speed_rpm=r.flow_m3h * 5)
                self._valves[wid].set_state(v_state)

    def _show_login_screen(self):
        from gui.login_dialog import LoginDialog
        LoginDialog(self._root, self._on_login_success)

    def _on_login_success(self, username: str, session):
        self._session_id = session.session_id
        self._logged_in_user = username
        self.lbl_user.config(text=f"👤 {username}")
        self._root.deiconify()
        from security.audit import AuditLogger
        AuditLogger.log_event("Session Init", "hmi", "SUCCESS", "INFO", username, session.session_id, details="HMI console opened")
        self._check_session_timeout()


    def _logout(self):
        if self._session_id:
            from security.session_manager import SessionManager
            from security.audit import AuditLogger
            AuditLogger.log_event("Logout", "hmi", "SUCCESS", "INFO", self._logged_in_user, self._session_id, details="User initiated logout")
            SessionManager().terminate_session(self._session_id)
            self._session_id = None
            self._logged_in_user = None
            self.lbl_user.config(text="")
            self._root.withdraw()
            self._show_login_screen()


    def _reset_activity_timer(self, event=None):
        if self._session_id:
            from security.session_manager import SessionManager
            SessionManager().validate_session(self._session_id)

    def _check_session_timeout(self):
        if self._session_id:
            from security.session_manager import SessionManager
            is_valid = SessionManager().validate_session(self._session_id)
            if not is_valid:
                from security.audit import AuditLogger
                AuditLogger.log_event("Session Timeout", "hmi", "EXPIRED", "WARN", self._logged_in_user, self._session_id, details="Inactivity limit exceeded")
                self._session_id = None
                self._logged_in_user = None
                self.lbl_user.config(text="")
                self._root.withdraw()
                import tkinter.messagebox as mb
                mb.showwarning("Session Timeout", "You have been logged out due to inactivity.")
                self._show_login_screen()
                return
        self._root.after(5000, self._check_session_timeout)


    def run(self):
        from security.audit import AuditLogger
        logger.info("SCADA GUI starting.")
        if "events" in self._panels:
            self._panels["events"].add_event("system", "INFO", "GUI Application Started")
        if "events" in self._panels:
            self._panels["events"].add_event("system", "INFO", "Connecting to PLC data streams...")
        AuditLogger.log_event("Application Startup", "hmi", "SUCCESS", "INFO", details="SCADA interface initialized")
        self._root.after(100, self._tick)
        self._schedule_memory_monitoring()
        self._root.mainloop()

    def _schedule_memory_monitoring(self):
        from core.performance.memory_monitor import MemoryMonitor
        from core.configuration import config
        try:
            MemoryMonitor().check_memory_thresholds()
        except Exception as e:
            logger.debug(f"Memory check failed: {e}")
        interval_ms = int(config.get("performance.cleanup_interval_s", 300) * 1000)
        self._root.after(interval_ms, self._schedule_memory_monitoring)

    def _on_close_app(self):
        from security.audit import AuditLogger
        from core.performance.memory_monitor import MemoryMonitor
        AuditLogger.log_event("Application Shutdown", "hmi", "SUCCESS", "INFO", username=self._logged_in_user, session_id=self._session_id, details="SCADA window closed by user")
        
        logger.info("Initiating graceful shutdown sequence...")
        
        # Stop SCADA loop
        if hasattr(self, '_scada'):
            self._scada.stop()
            
        # Flush and close Historian explicitly
        if hasattr(self, '_historian'):
            self._historian.close()
            
        # Clean up data provider / sensor threads
        if hasattr(self, '_provider'):
            if hasattr(self._provider, 'disconnect'):
                self._provider.disconnect()
                
        # Stop background AI engines
        if hasattr(self, '_rul_engine') and hasattr(self._rul_engine, 'stop'):
            self._rul_engine.stop()
        if hasattr(self, '_opt_engine') and hasattr(self._opt_engine, 'stop'):
            self._opt_engine.stop()
        if hasattr(self, '_anomaly_engine') and hasattr(self._anomaly_engine, 'stop'):
            self._anomaly_engine.stop()
            
        try:
            MemoryMonitor().perform_cleanup()
        except Exception:
            pass
            
        logger.info("Shutdown sequence complete. Exiting UI.")
        self._root.destroy()


if __name__ == "__main__":
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
        
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    app = SCADAGuiApp(scan_interval=REFRESH_MS)
    app.run()
