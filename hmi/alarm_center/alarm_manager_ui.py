"""
hmi/alarm_center/alarm_manager_ui.py
====================================
Professional Industrial Operator Alarm Center.
"""

import tkinter as tk
import tkinter.ttk as ttk
from datetime import datetime, timedelta
import time
from gui.theme import BG_PRIMARY, BG_SECONDARY, BG_TERTIARY, BG_HEADER, BORDER, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, CLR_CRITICAL, CLR_WARNING, CLR_NORMAL, FONT_SUBTITLE, FONT_MONO_SM, FONT_LABEL, FONT_MONO_MD, FONT_LABEL_SM
from gui.i18n import tr
import tkinter.messagebox as messagebox

class AlarmCenterPanel(tk.Frame):
    def __init__(self, parent: tk.Widget, alarm_manager, on_navigate=None, on_explain_cb=None, **kwargs):
        super().__init__(parent, bg=BG_PRIMARY, **kwargs)
        self._alarm_manager = alarm_manager
        self.on_navigate = on_navigate
        self.on_explain_cb = on_explain_cb
        
        # UI Structure
        self._build_styles()
        self._build_summary_cards()
        
        body_frame = tk.Frame(self, bg=BG_PRIMARY)
        body_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        body_frame.columnconfigure(0, weight=75) # 75% width
        body_frame.columnconfigure(1, weight=25) # 25% width
        body_frame.rowconfigure(0, weight=1)
        
        self.left_frame = tk.Frame(body_frame, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        self.right_frame = tk.Frame(body_frame, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1)
        self.right_frame.grid(row=0, column=1, sticky="nsew")
        
        self._build_filter_panel(self.left_frame)
        self._build_main_table(self.left_frame)
        self._build_timeline(self.right_frame)
        
    def _build_styles(self):
        style = ttk.Style()
        style.configure("Alarm.Treeview", background=BG_SECONDARY, foreground=TEXT_PRIMARY, fieldbackground=BG_SECONDARY, rowheight=30, borderwidth=0)
        style.map("Alarm.Treeview", background=[("selected", BG_HEADER)])
        style.configure("Alarm.Treeview.Heading", background=BG_HEADER, foreground=TEXT_SECONDARY, font=FONT_LABEL)
        
    def _build_summary_cards(self):
        self.summary_frame = tk.Frame(self, bg=BG_PRIMARY)
        self.summary_frame.pack(fill="x", padx=20, pady=15)
        
        self.cards = {}
        cards_info = [
            ("Total Active Alarms", "#1f2937", TEXT_PRIMARY),
            ("Critical Alarms", "#450a0a", CLR_CRITICAL),
            ("Warnings", "#422006", CLR_WARNING),
            ("Acknowledged", "#064e3b", "#10b981"),
            ("AI Related", "#1e3a8a", "#60a5fa"),
            ("Last Alarm Time", BG_TERTIARY, TEXT_SECONDARY)
        ]
        
        for i, (title, bg_col, fg_col) in enumerate(cards_info):
            self.summary_frame.columnconfigure(i, weight=1, uniform="card")
            card = tk.Frame(self.summary_frame, bg=bg_col, highlightbackground=BORDER, highlightthickness=1)
            card.grid(row=0, column=i, sticky="nsew", padx=5)
            
            lbl_title = tk.Label(card, text=title, bg=bg_col, fg=TEXT_SECONDARY, font=FONT_LABEL_SM, anchor="w")
            lbl_title.pack(side="top", fill="x", padx=10, pady=(8, 0))
            
            lbl_val = tk.Label(card, text="-", bg=bg_col, fg=fg_col, font=FONT_SUBTITLE, anchor="w")
            lbl_val.pack(side="top", fill="x", padx=10, pady=(0, 8))
            
            self.cards[title] = lbl_val

    def _build_filter_panel(self, parent):
        filter_bar = tk.Frame(parent, bg=BG_HEADER)
        filter_bar.pack(fill="x")
        
        # Search
        tk.Label(filter_bar, text="Search:", bg=BG_HEADER, fg=TEXT_SECONDARY, font=FONT_LABEL).pack(side="left", padx=(10, 5), pady=10)
        self.var_search = tk.StringVar()
        ent = tk.Entry(filter_bar, textvariable=self.var_search, bg=BG_SECONDARY, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY, width=15)
        ent.pack(side="left")
        ent.bind("<KeyRelease>", lambda e: self.update_alarms())
        
        # Severity
        tk.Label(filter_bar, text="Severity:", bg=BG_HEADER, fg=TEXT_SECONDARY, font=FONT_LABEL).pack(side="left", padx=(15, 5))
        self.cb_severity = ttk.Combobox(filter_bar, values=["ALL", "CRITICAL", "HIGH", "WARNING", "INFO"], state="readonly", width=10)
        self.cb_severity.current(0)
        self.cb_severity.pack(side="left")
        self.cb_severity.bind("<<ComboboxSelected>>", lambda e: self.update_alarms())
        
        # Checkboxes
        self.var_active = tk.BooleanVar(value=True)
        self.var_acked = tk.BooleanVar(value=True)
        self.var_cleared = tk.BooleanVar(value=False)
        self.var_ai = tk.BooleanVar(value=False)
        
        chk_style = {"bg": BG_HEADER, "fg": TEXT_PRIMARY, "selectcolor": BG_SECONDARY, "activebackground": BG_HEADER, "activeforeground": TEXT_PRIMARY}
        
        tk.Checkbutton(filter_bar, text="Active", variable=self.var_active, command=self.update_alarms, **chk_style).pack(side="left", padx=(15, 5))
        tk.Checkbutton(filter_bar, text="Acked", variable=self.var_acked, command=self.update_alarms, **chk_style).pack(side="left", padx=5)
        tk.Checkbutton(filter_bar, text="Cleared", variable=self.var_cleared, command=self.update_alarms, **chk_style).pack(side="left", padx=5)
        tk.Checkbutton(filter_bar, text="AI Related", variable=self.var_ai, command=self.update_alarms, **chk_style).pack(side="left", padx=5)
        
        # Ack button
        tk.Button(filter_bar, text="Acknowledge Selected", bg=BG_SECONDARY, fg=TEXT_PRIMARY, relief="flat", command=self._ack_selected).pack(side="right", padx=10)

    def _build_main_table(self, parent):
        columns = ("Severity", "Time", "Equipment", "Tag", "Description", "Status", "Acknowledged", "Operator", "Duration")
        self.tree_main = ttk.Treeview(parent, columns=columns, show="headings", style="Alarm.Treeview")
        
        widths = {
            "Severity": 80,
            "Time": 90,
            "Equipment": 100,
            "Tag": 140,
            "Description": 300,
            "Status": 100,
            "Acknowledged": 90,
            "Operator": 80,
            "Duration": 80
        }
        
        for col in columns:
            self.tree_main.heading(col, text=col, command=lambda c=col: self._sort_tree(c, False))
            self.tree_main.column(col, width=widths.get(col, 100), anchor="w" if col == "Description" else "center")
            
        # ISA-18.2 Colors
        self.tree_main.tag_configure("CRITICAL", background="#450a0a", foreground="#fca5a5")
        self.tree_main.tag_configure("HIGH", background="#431407", foreground="#fdba74")
        self.tree_main.tag_configure("WARNING", background="#422006", foreground="#fde047")
        self.tree_main.tag_configure("INFO", background="#1e3a8a", foreground="#93c5fd")
        self.tree_main.tag_configure("CLEARED", foreground=TEXT_SECONDARY)
        
        self.tree_main.pack(fill="both", expand=True)
        self.tree_main.bind("<Double-1>", self._on_tree_double_click)
        self.tree_main.bind("<Button-3>", self._show_context_menu)
        
        # Build Context Menu
        self.context_menu = tk.Menu(self, tearoff=0, bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_LABEL_SM)
        self.context_menu.add_command(label="Explain AI Decision", command=self._explain_selected)

    def _build_timeline(self, parent):
        tk.Label(parent, text="Event Timeline", bg=BG_HEADER, fg=TEXT_PRIMARY, font=FONT_LABEL, anchor="w", padx=15, pady=10).pack(fill="x")
        
        self.tree_timeline = ttk.Treeview(parent, columns=("Time", "Type", "Details"), show="headings", style="Alarm.Treeview")
        self.tree_timeline.heading("Time", text="Time")
        self.tree_timeline.column("Time", width=70, anchor="center")
        self.tree_timeline.heading("Type", text="Type")
        self.tree_timeline.column("Type", width=90, anchor="center")
        self.tree_timeline.heading("Details", text="Details")
        self.tree_timeline.column("Details", width=150, anchor="w")
        
        self.tree_timeline.tag_configure("RAISED", foreground="#fca5a5")
        self.tree_timeline.tag_configure("ACKED", foreground="#6ee7b7")
        self.tree_timeline.tag_configure("CLEARED", foreground=TEXT_SECONDARY)
        self.tree_timeline.tag_configure("AI", foreground="#93c5fd")
        self.tree_timeline.tag_configure("SYSTEM", foreground="#fde047")
        
        self.tree_timeline.pack(fill="both", expand=True)

    # ==========================================
    # LOGIC
    # ==========================================

    def _sort_tree(self, col, reverse):
        l = [(self.tree_main.set(k, col), k) for k in self.tree_main.get_children('')]
        l.sort(reverse=reverse)
        for index, (val, k) in enumerate(l):
            self.tree_main.move(k, '', index)
        self.tree_main.heading(col, command=lambda: self._sort_tree(col, not reverse))

    def _on_tree_double_click(self, event):
        sel = self.tree_main.selection()
        if not sel: return
        item = self.tree_main.item(sel[0], "values")
        if not item: return
        
        # Col 3 is Tag
        tag_id = item[3]
        if tag_id:
            self._navigate_to_equipment(tag_id)

    def _navigate_to_equipment(self, equipment_id: str):
        from digital_twin.visualization.popups import EquipmentDetailPopup
        # Usually Equipment id is the prefix
        eq_id = equipment_id.split('_')[0]
        EquipmentDetailPopup.get_or_create(self.winfo_toplevel(), eq_id, "Equipment")
        if self.on_navigate:
            self.on_navigate(eq_id)
            
    def _show_context_menu(self, event):
        item = self.tree_main.identify_row(event.y)
        if item:
            self.tree_main.selection_set(item)
            self.context_menu.tk_popup(event.x_root, event.y_root)
            
    def _explain_selected(self):
        sel = self.tree_main.selection()
        if not sel: return
        item_vals = self.tree_main.item(sel[0], "values")
        # Col 2 is Equipment
        equipment_id = item_vals[2]
        if self.on_explain_cb:
            self.on_explain_cb(equipment_id)

    def _ack_selected(self):
        sel = self.tree_main.selection()
        for item in sel:
            tag_id = self.tree_main.item(item, "values")[3]
            # Find the alarm id from tag id
            for a in self._alarm_manager.active_alarms:
                if a.tag_id == tag_id:
                    self._alarm_manager.acknowledge(a.alarm_id)
        self.update_alarms()

    def _passes_filter(self, alarm) -> bool:
        search_txt = self.var_search.get().lower()
        if search_txt:
            eq = alarm.tag_id.split('_')[0].lower()
            if search_txt not in alarm.tag_id.lower() and \
               search_txt not in alarm.description.lower() and \
               search_txt not in eq:
                return False
                
        sev_filter = self.cb_severity.get()
        if sev_filter != "ALL" and alarm.priority.name != sev_filter:
            return False
            
        if self.var_ai.get() and alarm.category.name != "PREDICTIVE_AI":
            return False
            
        is_active = alarm.state.name == "ACTIVE"
        is_acked = alarm.state.name == "ACKNOWLEDGED"
        is_cleared = alarm.state.name == "CLEARED"
        
        # If none of the status checkboxes are checked, show nothing, else check if it matches ANY of the checked ones
        if not self.var_active.get() and not self.var_acked.get() and not self.var_cleared.get():
            return False
            
        match = False
        if self.var_active.get() and is_active: match = True
        if self.var_acked.get() and is_acked: match = True
        if self.var_cleared.get() and is_cleared: match = True
        
        if not match: return False
            
        return True

    def update_alarms(self):
        # 1. Gather all alarms
        all_alarms = list(self._alarm_manager.active_alarms) + self._alarm_manager.alarm_history
        
        # 2. Update Summary Cards
        active = sum(1 for a in self._alarm_manager.active_alarms)
        crit = sum(1 for a in self._alarm_manager.active_alarms if a.priority.name == "CRITICAL")
        warn = sum(1 for a in self._alarm_manager.active_alarms if a.priority.name == "WARNING")
        acked = sum(1 for a in self._alarm_manager.active_alarms if a.state.name == "ACKNOWLEDGED")
        ai_rel = sum(1 for a in self._alarm_manager.active_alarms if a.category.name == "PREDICTIVE_AI")
        
        last_t = "-"
        if all_alarms:
            latest = max(a.triggered_at for a in all_alarms)
            last_t = datetime.fromtimestamp(latest).strftime("%H:%M:%S")
            
        self.cards["Total Active Alarms"].config(text=str(active))
        self.cards["Critical Alarms"].config(text=str(crit))
        self.cards["Warnings"].config(text=str(warn))
        self.cards["Acknowledged"].config(text=str(acked))
        self.cards["AI Related"].config(text=str(ai_rel))
        self.cards["Last Alarm Time"].config(text=last_t)
        
        # 3. Update Main Table
        # Retain selection
        sel_tags = [self.tree_main.item(i, "values")[3] for i in self.tree_main.selection() if self.tree_main.item(i, "values")]
        
        for item in self.tree_main.get_children(): self.tree_main.delete(item)
        
        # Sort newest first for display
        display_alarms = sorted(all_alarms, key=lambda x: x.triggered_at, reverse=True)
        
        for a in display_alarms:
            if not self._passes_filter(a): continue
            
            ts = datetime.fromtimestamp(a.triggered_at).strftime("%m-%d %H:%M:%S")
            eq = a.tag_id.split('_')[0]
            ack_ts = datetime.fromtimestamp(a.acknowledged_at).strftime("%H:%M:%S") if a.acknowledged_at else "-"
            
            # Format duration
            dur_m, dur_s = divmod(int(a.age_seconds), 60)
            dur_h, dur_m = divmod(dur_m, 60)
            dur_str = f"{dur_h:02d}:{dur_m:02d}:{dur_s:02d}" if a.age_seconds > 0 else "-"
            
            tag_col = a.priority.name if a.state.name != "CLEARED" else "CLEARED"
            
            icon = "🚨" if a.priority.name == "CRITICAL" else "⚠️" if a.priority.name in ["HIGH", "WARNING"] else "ℹ️"
            
            item_id = self.tree_main.insert("", "end", values=(
                f"{icon} {a.priority.name}", ts, eq, a.tag_id, a.description, a.state.name, 
                ack_ts, a.operator or "-", dur_str
            ), tags=(tag_col,))
            
            if a.tag_id in sel_tags:
                self.tree_main.selection_add(item_id)
                
        # 4. Update Event Timeline
        for item in self.tree_timeline.get_children(): self.tree_timeline.delete(item)
        
        timeline_events = []
        for a in all_alarms:
            timeline_events.append((a.triggered_at, "RAISED", f"{a.tag_id} Raised"))
            if a.acknowledged_at:
                timeline_events.append((a.acknowledged_at, "ACKED", f"{a.tag_id} Ack'd"))
            if a.cleared_at:
                timeline_events.append((a.cleared_at, "CLEARED", f"{a.tag_id} Cleared"))
                
        for e in self._alarm_manager.event_history:
            t_type = "AI" if "AI" in e.category else "SYSTEM"
            timeline_events.append((e.timestamp, t_type, f"{e.equipment} {e.description}"))
            
        timeline_events.sort(key=lambda x: x[0], reverse=True)
        
        for t, typ, desc in timeline_events[:50]: # Show last 50 events
            ts = datetime.fromtimestamp(t).strftime("%H:%M:%S")
            self.tree_timeline.insert("", "end", values=(ts, typ, desc), tags=(typ,))
