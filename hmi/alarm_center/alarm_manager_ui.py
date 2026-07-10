"""
hmi/alarm_center/alarm_manager_ui.py
====================================
Professional Industrial Operator Alarm Center.
"""

import tkinter as tk
import tkinter.ttk as ttk
from datetime import datetime
from gui.theme import BG_PRIMARY, BG_SECONDARY, BG_HEADER, BORDER, TEXT_PRIMARY, TEXT_SECONDARY, CLR_CRITICAL, CLR_WARNING, CLR_NORMAL, FONT_SUBTITLE, FONT_MONO_SM, FONT_LABEL, FONT_MONO_MD
from gui.i18n import tr
import tkinter.messagebox as messagebox

# Matplotlib for Trend Analytics
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class AlarmCenterPanel(tk.Frame):
    def __init__(self, parent: tk.Widget, alarm_manager, on_navigate=None, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, **kwargs)
        self._alarm_manager = alarm_manager
        self.on_navigate = on_navigate
        
        # Priority Dashboard (KPI Top Bar)
        self._build_priority_dashboard()
        
        # Global Search & Filters Toolbar
        self._build_filter_bar()
        
        # Style definition
        style = ttk.Style()
        style.configure("Alarm.TNotebook", background=BG_PRIMARY, borderwidth=0)
        style.configure("Alarm.TNotebook.Tab", background=BG_SECONDARY, foreground=TEXT_PRIMARY, padding=[10, 5], font=FONT_LABEL)
        style.map("Alarm.TNotebook.Tab", background=[("selected", BG_HEADER)])
        
        style.configure("Alarm.Treeview", background=BG_SECONDARY, foreground=TEXT_PRIMARY, fieldbackground=BG_SECONDARY, rowheight=30)
        style.map("Alarm.Treeview", background=[("selected", BG_HEADER)])
        
        self.notebook = ttk.Notebook(self, style="Alarm.TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self._build_alarm_views()
        self._build_equipment_tab()
        self._build_history_tab()
        self._build_event_tab()
        self._build_timeline_tab()
        self._build_analytics_tab()
        
    def _build_priority_dashboard(self):
        frame = tk.Frame(self, bg=BG_SECONDARY)
        frame.pack(fill="x", padx=20, pady=(10, 5))
        
        lbl = tk.Label(frame, text=tr("OPERATOR ALARM CENTER"), bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_SUBTITLE)
        lbl.pack(side="left", padx=10, pady=10)
        
        self.lbl_crit = tk.Label(frame, text="CRITICAL: 0", bg="#450a0a", fg="#f87171", font=FONT_SUBTITLE, padx=10, pady=5)
        self.lbl_crit.pack(side="right", padx=5, pady=5)
        self.lbl_high = tk.Label(frame, text="HIGH: 0", bg="#451a03", fg="#fb923c", font=FONT_SUBTITLE, padx=10, pady=5)
        self.lbl_high.pack(side="right", padx=5, pady=5)
        self.lbl_warn = tk.Label(frame, text="WARNING: 0", bg="#422006", fg="#fcd34d", font=FONT_SUBTITLE, padx=10, pady=5)
        self.lbl_warn.pack(side="right", padx=5, pady=5)
        self.lbl_info = tk.Label(frame, text="INFO: 0", bg=BG_PRIMARY, fg=TEXT_SECONDARY, font=FONT_SUBTITLE, padx=10, pady=5)
        self.lbl_info.pack(side="right", padx=5, pady=5)

    def _build_filter_bar(self):
        from core.config.system_config import SystemConfig
        self._config = SystemConfig.load()
        
        frame = tk.Frame(self, bg=BG_PRIMARY)
        frame.pack(fill="x", padx=20, pady=(0, 10))
        
        tk.Label(frame, text="Search:", bg=BG_PRIMARY, fg=TEXT_PRIMARY, font=FONT_LABEL).pack(side="left")
        self.var_search = tk.StringVar()
        ent = tk.Entry(frame, textvariable=self.var_search, bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_LABEL, insertbackground=TEXT_PRIMARY, width=20)
        ent.pack(side="left", padx=5)
        ent.bind("<KeyRelease>", self._on_filter_change)
        
        tk.Label(frame, text="Severity:", bg=BG_PRIMARY, fg=TEXT_PRIMARY, font=FONT_LABEL).pack(side="left", padx=(15,0))
        self.cb_severity = ttk.Combobox(frame, values=["ALL", "CRITICAL", "HIGH", "WARNING", "INFO"], state="readonly", width=10)
        
        # Load from config
        saved_severity = getattr(self._config.workspace, "alarm_filter_severity", "ALL")
        if saved_severity in self.cb_severity["values"]:
            self.cb_severity.set(saved_severity)
        else:
            self.cb_severity.current(0)
            
        self.cb_severity.pack(side="left", padx=5)
        self.cb_severity.bind("<<ComboboxSelected>>", self._on_filter_change)

    def _on_filter_change(self, event=None):
        self._config.workspace.alarm_filter_severity = self.cb_severity.get()
        self.update_alarms()

    def _build_alarm_views(self):
        # ACTIVE TAB
        self.frm_active = tk.Frame(self.notebook, bg=BG_PRIMARY)
        self.notebook.add(self.frm_active, text=tr("Active Alarms"))
        
        actions_act = tk.Frame(self.frm_active, bg=BG_PRIMARY)
        actions_act.pack(fill="x", pady=10)
        tk.Button(actions_act, text=tr("Acknowledge Selected"), bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_LABEL, relief="flat", command=self._ack_selected).pack(side="left", padx=(0, 10))
        tk.Button(actions_act, text=tr("Acknowledge All"), bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_LABEL, relief="flat", command=self._ack_all).pack(side="left")
        
        # ACKNOWLEDGED TAB
        self.frm_acked = tk.Frame(self.notebook, bg=BG_PRIMARY)
        self.notebook.add(self.frm_acked, text=tr("Acknowledged Alarms"))
        
        # CLEARED TAB
        self.frm_cleared = tk.Frame(self.notebook, bg=BG_PRIMARY)
        self.notebook.add(self.frm_cleared, text=tr("Cleared Alarms"))
        
        columns = (tr("Timestamp"), tr("ID"), tr("Tag"), tr("Description"), tr("Priority"), tr("Status"))
        
        self.tree_active = self._create_alarm_tree(self.frm_active, columns)
        self.tree_acked = self._create_alarm_tree(self.frm_acked, columns)
        self.tree_cleared = self._create_alarm_tree(self.frm_cleared, columns)

    def _create_alarm_tree(self, parent, columns):
        tree = ttk.Treeview(parent, columns=columns, show="headings", style="Alarm.Treeview", height=15)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120 if col != tr("Description") else 350)
            
        tree.pack(fill="both", expand=True)
        tree.tag_configure("CRITICAL", background="#450a0a", foreground="#f87171")
        tree.tag_configure("HIGH", background="#451a03", foreground="#fb923c")
        tree.tag_configure("WARNING", background="#422006", foreground="#fcd34d")
        tree.tag_configure("INFO", background=BG_SECONDARY, foreground=TEXT_SECONDARY)
        tree.bind("<Double-1>", self._on_tree_double_click)
        return tree

    def _build_equipment_tab(self):
        frame = tk.Frame(self.notebook, bg=BG_PRIMARY)
        self.notebook.add(frame, text=tr("Equipment View"))
        
        self.paned = tk.PanedWindow(frame, orient=tk.HORIZONTAL, bg=BORDER, bd=0, sashwidth=2)
        self.paned.pack(fill="both", expand=True, pady=10)
        
        # Left: List of Equipments
        left_frm = tk.Frame(self.paned, bg=BG_SECONDARY)
        self.paned.add(left_frm, minsize=150)
        
        tk.Label(left_frm, text=tr("Equipments"), bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_LABEL).pack(pady=5)
        self.lb_equipment = tk.Listbox(left_frm, bg=BG_PRIMARY, fg=TEXT_PRIMARY, font=FONT_MONO_MD, bd=0, highlightthickness=0)
        self.lb_equipment.pack(fill="both", expand=True, padx=5, pady=5)
        self.lb_equipment.bind("<<ListboxSelect>>", self._on_equipment_select)
        
        # Right: Details
        right_frm = tk.Frame(self.paned, bg=BG_PRIMARY)
        self.paned.add(right_frm, minsize=400)
        
        # We'll put a mini-notebook here
        self.eq_notebook = ttk.Notebook(right_frm, style="Alarm.TNotebook")
        self.eq_notebook.pack(fill="both", expand=True)
        
        # Sub-tab: Alarms
        frm_eq_alarms = tk.Frame(self.eq_notebook, bg=BG_PRIMARY)
        self.eq_notebook.add(frm_eq_alarms, text="Alarms")
        self.tree_eq_alarms = ttk.Treeview(frm_eq_alarms, columns=("Time", "Alarm", "Status"), show="headings", style="Alarm.Treeview", height=10)
        for c in ("Time", "Alarm", "Status"): self.tree_eq_alarms.heading(c, text=c)
        self.tree_eq_alarms.pack(fill="both", expand=True, pady=5)
        
        # Sub-tab: Events
        frm_eq_events = tk.Frame(self.eq_notebook, bg=BG_PRIMARY)
        self.eq_notebook.add(frm_eq_events, text="Events")
        self.tree_eq_events = ttk.Treeview(frm_eq_events, columns=("Time", "Category", "Description"), show="headings", style="Alarm.Treeview", height=10)
        for c in ("Time", "Category", "Description"): self.tree_eq_events.heading(c, text=c)
        self.tree_eq_events.pack(fill="both", expand=True, pady=5)

    def _build_history_tab(self):
        frame = tk.Frame(self.notebook, bg=BG_PRIMARY)
        self.notebook.add(frame, text=tr("Alarm History"))
        
        actions = tk.Frame(frame, bg=BG_PRIMARY)
        actions.pack(fill="x", pady=10)
        
        tk.Button(actions, text=tr("Export CSV"), bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_LABEL, relief="flat", command=self._export_alarms).pack(side="right")
        
        columns = (tr("Timestamp"), tr("Tag"), tr("Priority"), tr("Status"), tr("Duration (s)"), tr("Cleared At"))
        self.tree_hist = ttk.Treeview(frame, columns=columns, show="headings", style="Alarm.Treeview", height=15)
        for col in columns:
            self.tree_hist.heading(col, text=col)
        self.tree_hist.pack(fill="both", expand=True)
        self.tree_hist.bind("<Double-1>", self._on_tree_double_click)

    def _build_event_tab(self):
        frame = tk.Frame(self.notebook, bg=BG_PRIMARY)
        self.notebook.add(frame, text=tr("Event History"))
        
        actions = tk.Frame(frame, bg=BG_PRIMARY)
        actions.pack(fill="x", pady=10)
        
        tk.Button(actions, text=tr("Export CSV"), bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_LABEL, relief="flat", command=self._export_events).pack(side="right")
        
        columns = (tr("Timestamp"), tr("Category"), tr("Equipment"), tr("Description"))
        self.tree_events = ttk.Treeview(frame, columns=columns, show="headings", style="Alarm.Treeview", height=15)
        for col in columns:
            self.tree_events.heading(col, text=col)
            self.tree_events.column(col, width=150 if col != tr("Description") else 400)
        self.tree_events.pack(fill="both", expand=True)

    def _build_timeline_tab(self):
        frame = tk.Frame(self.notebook, bg=BG_PRIMARY)
        self.notebook.add(frame, text=tr("Alarm Timeline"))
        
        columns = (tr("Event Phase"), tr("Alarm ID"), tr("Time"), tr("Operator/System"))
        self.tree_timeline = ttk.Treeview(frame, columns=columns, show="headings", style="Alarm.Treeview", height=15)
        for col in columns:
            self.tree_timeline.heading(col, text=col)
        self.tree_timeline.pack(fill="both", expand=True, pady=10)

    def _build_analytics_tab(self):
        frame = tk.Frame(self.notebook, bg=BG_PRIMARY)
        self.notebook.add(frame, text=tr("Trend Analytics"))
        
        self.fig = Figure(figsize=(8, 4), dpi=100, facecolor=BG_PRIMARY)
        # We will use 2 subplots for now
        self.ax_bar = self.fig.add_subplot(121)
        self.ax_pie = self.fig.add_subplot(122)
        
        self.fig.subplots_adjust(bottom=0.2, wspace=0.3)
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, pady=10)

    # ==========================================
    # LOGIC
    # ==========================================

    def _on_tree_double_click(self, event):
        """One-Click Navigation to Equipment"""
        tree = event.widget
        sel = tree.selection()
        if not sel: return
        item = tree.item(sel[0], "values")
        if len(item) < 3: return
        
        # Attempt to extract equipment Tag/ID from the Treeview
        tag_id = None
        if hasattr(self, "tree_active") and tree in (self.tree_active, getattr(self, "tree_acked", None), getattr(self, "tree_cleared", None)):
            tag_id = item[2]
        elif hasattr(self, "tree_hist") and tree == self.tree_hist:
            tag_id = item[1]
            
        if tag_id:
            self._navigate_to_equipment(tag_id)

    def _navigate_to_equipment(self, equipment_id: str):
        """
        Navigates the Digital Twin dashboard to focus on the equipment.
        Opens detailed diagnostic popup directly and prepares AI hooks.
        """
        logger = __import__('logging').getLogger(__name__)
        logger.info(f"Opening equipment details for: {equipment_id}")
        
        from digital_twin.visualization.popups import EquipmentDetailPopup
        EquipmentDetailPopup.get_or_create(self.winfo_toplevel(), equipment_id, "Equipment")
        
        # Prepare hooks for future AI recommendations
        self._prepare_ai_recommendation_hook(equipment_id)
        
        if self.on_navigate:
            self.on_navigate(equipment_id)

    def _prepare_ai_recommendation_hook(self, equipment_id: str):
        """
        STUB: Future integration point for AI-assisted operator guidance.
        Will cross-reference the active alarm with fault trees and RUL models.
        """
        pass

    def _ack_selected(self):
        # Acknowledge multi-selected items in the active tree
        if not hasattr(self, "tree_active"): return
        for item in self.tree_active.selection():
            alarm_id = self.tree_active.item(item, "values")[1]
            self._alarm_manager.acknowledge(alarm_id)
        # Update immediately to reflect changes in tabs
        self.update_alarms()
                
    def _ack_all(self):
        for alarm in self._alarm_manager.active_alarms:
            if alarm.state.name == "ACTIVE":
                self._alarm_manager.acknowledge(alarm.alarm_id)
        self.update_alarms()

    def _export_alarms(self):
        path = self._alarm_manager.export_alarms_csv()
        messagebox.showinfo("Export Success", f"Alarms exported to:\n{path}")

    def _export_events(self):
        path = self._alarm_manager.export_events_csv()
        messagebox.showinfo("Export Success", f"Events exported to:\n{path}")

    def _on_equipment_select(self, event):
        sel = self.lb_equipment.curselection()
        if not sel: return
        eq = self.lb_equipment.get(sel[0])
        self._update_equipment_view(eq)

    def _update_equipment_view(self, eq: str):
        # Clear sub-trees
        for item in self.tree_eq_alarms.get_children(): self.tree_eq_alarms.delete(item)
        for item in self.tree_eq_events.get_children(): self.tree_eq_events.delete(item)
        
        all_alarms = list(self._alarm_manager.active_alarms) + self._alarm_manager.alarm_history
        all_events = self._alarm_manager.event_history
        
        for a in reversed(all_alarms):
            if a.tag_id == eq:
                ts = datetime.fromtimestamp(a.triggered_at).strftime("%H:%M:%S")
                self.tree_eq_alarms.insert("", "end", values=(ts, a.alarm_id, a.state.value))
                
        for e in reversed(all_events):
            if e.equipment == eq:
                ts = datetime.fromtimestamp(e.timestamp).strftime("%H:%M:%S")
                self.tree_eq_events.insert("", "end", values=(ts, e.category, e.description))

    def _passes_filter(self, alarm) -> bool:
        search_txt = self.var_search.get().lower()
        if search_txt:
            if search_txt not in alarm.tag_id.lower() and \
               search_txt not in alarm.alarm_id.lower() and \
               search_txt not in alarm.description.lower():
                return False
                
        sev_filter = self.cb_severity.get()
        if sev_filter != "ALL" and alarm.priority.name != sev_filter:
            return False
            
        return True

    def _passes_event_filter(self, evt) -> bool:
        search_txt = self.var_search.get().lower()
        if search_txt:
            if search_txt not in evt.equipment.lower() and \
               search_txt not in evt.category.lower() and \
               search_txt not in evt.description.lower():
                return False
        return True

    def update_alarms(self):
        # 0. Update Priority Dashboard
        stats = self._alarm_manager.get_statistics()
        dist = stats.get("distribution", {})
        self.lbl_crit.config(text=f"CRITICAL: {dist.get('CRITICAL', 0)}")
        self.lbl_high.config(text=f"HIGH: {dist.get('HIGH', 0)}")
        self.lbl_warn.config(text=f"WARNING: {dist.get('WARNING', 0)}")
        self.lbl_info.config(text=f"INFO: {dist.get('INFO', 0)}")

        # 1. Update Active, Acknowledged, and Cleared Alarms
        for tree in (self.tree_active, self.tree_acked, self.tree_cleared):
            for item in tree.get_children(): tree.delete(item)
            
        all_alarms = list(self._alarm_manager.active_alarms) + self._alarm_manager.alarm_history
        
        for alarm in all_alarms:
            if not self._passes_filter(alarm): continue
            
            ts = datetime.fromtimestamp(alarm.triggered_at).strftime("%H:%M:%S")
            vals = (ts, alarm.alarm_id, alarm.tag_id, alarm.description, alarm.priority.name, alarm.state.value)
            
            if alarm.state.name == "ACTIVE":
                self.tree_active.insert("", "end", values=vals, tags=(alarm.priority.name,))
            elif alarm.state.name == "ACKNOWLEDGED":
                self.tree_acked.insert("", "end", values=vals, tags=(alarm.priority.name,))
            elif alarm.state.name == "CLEARED":
                self.tree_cleared.insert("", "end", values=vals, tags=(alarm.priority.name,))

        # 2. Update Alarm History
        for item in self.tree_hist.get_children(): self.tree_hist.delete(item)
        for alarm in reversed(self._alarm_manager.alarm_history[-200:]):
            if not self._passes_filter(alarm): continue
            ts = datetime.fromtimestamp(alarm.triggered_at).strftime("%H:%M:%S")
            clr = datetime.fromtimestamp(alarm.cleared_at).strftime("%H:%M:%S") if alarm.cleared_at else "-"
            self.tree_hist.insert("", "end", values=(
                ts, alarm.tag_id, alarm.priority.name, alarm.state.value, f"{alarm.age_seconds:.1f}", clr
            ))

        # 3. Update Event History
        for item in self.tree_events.get_children(): self.tree_events.delete(item)
        for evt in reversed(self._alarm_manager.event_history[-200:]):
            if not self._passes_event_filter(evt): continue
            ts = datetime.fromtimestamp(evt.timestamp).strftime("%H:%M:%S")
            self.tree_events.insert("", "end", values=(
                ts, evt.category, evt.equipment, evt.description
            ))

        # 4. Update Timeline (Unfiltered chronological view of alarms)
        for item in self.tree_timeline.get_children(): self.tree_timeline.delete(item)
        all_alarms = list(self._alarm_manager.active_alarms) + self._alarm_manager.alarm_history
        all_alarms.sort(key=lambda a: a.triggered_at, reverse=True)
        for a in all_alarms[:30]:
            if not self._passes_filter(a): continue
            
            # If cleared, show cleared event
            if a.cleared_at:
                ts = datetime.fromtimestamp(a.cleared_at).strftime("%H:%M:%S")
                self.tree_timeline.insert("", "end", values=("CLEARED", a.alarm_id, ts, "SYSTEM"))
                
            # If acked, show ack event
            if a.acknowledged_at:
                ts = datetime.fromtimestamp(a.acknowledged_at).strftime("%H:%M:%S")
                self.tree_timeline.insert("", "end", values=("ACKNOWLEDGED", a.alarm_id, ts, a.operator or "SYSTEM"))
                
            # Triggered event
            ts = datetime.fromtimestamp(a.triggered_at).strftime("%H:%M:%S")
            self.tree_timeline.insert("", "end", values=("TRIGGERED", a.alarm_id, ts, "SYSTEM"))

        # 5. Update Equipments Listbox silently
        eqs = set()
        for a in all_alarms: eqs.add(a.tag_id)
        current_eqs = self.lb_equipment.get(0, "end")
        if set(current_eqs) != eqs:
            self.lb_equipment.delete(0, "end")
            for eq in sorted(list(eqs)):
                self.lb_equipment.insert("end", eq)

        # Update currently selected equipment view
        sel = self.lb_equipment.curselection()
        if sel:
            self._update_equipment_view(self.lb_equipment.get(sel[0]))

        # 6. Update Analytics
        self._update_analytics(stats)

    def _update_analytics(self, stats):
        self.ax_bar.clear()
        self.ax_pie.clear()
        
        self.ax_bar.set_facecolor(BG_PRIMARY)
        self.ax_pie.set_facecolor(BG_PRIMARY)
        
        # Color mapping matching UI
        colors = {"CRITICAL": "#f87171", "HIGH": "#fb923c", "WARNING": "#fcd34d", "INFO": "#9ca3af"}
        
        dist = stats.get("distribution", {})
        labels = [k for k, v in dist.items() if v > 0]
        sizes = [v for v in dist.values() if v > 0]
        c_list = [colors.get(l, "white") for l in labels]
        
        if sizes:
            self.ax_pie.axis('on')
            self.ax_pie.pie(sizes, labels=labels, colors=c_list, autopct='%1.1f%%', textprops={'color': TEXT_PRIMARY})
            self.ax_pie.set_title("Alarm Distribution", color=TEXT_SECONDARY)
        else:
            self.ax_pie.axis('off')
            self.ax_pie.text(0.5, 0.5, "No Alarm Distribution Data", 
                             horizontalalignment='center', verticalalignment='center',
                             transform=self.ax_pie.transAxes, color=TEXT_SECONDARY, fontsize=12)
        
        # Equipment counts
        eq_counts = self._alarm_manager._equipment_counts
        if eq_counts:
            self.ax_bar.axis('on')
            # top 5
            top = sorted(eq_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            x = [t[0] for t in top]
            y = [t[1] for t in top]
            bars = self.ax_bar.bar(x, y, color="#3b82f6")
            self.ax_bar.set_title("Top 5 Equipments", color=TEXT_SECONDARY)
            self.ax_bar.tick_params(colors=TEXT_SECONDARY)
            for spine in self.ax_bar.spines.values():
                spine.set_color(BORDER)
        else:
            self.ax_bar.axis('off')
            self.ax_bar.text(0.5, 0.5, "No Equipment Alarm Data", 
                             horizontalalignment='center', verticalalignment='center',
                             transform=self.ax_bar.transAxes, color=TEXT_SECONDARY, fontsize=12)
                
        self.fig.patch.set_facecolor(BG_PRIMARY)
        self.canvas.draw()
