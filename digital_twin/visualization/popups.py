"""
gui/interactive.py
==================
Interactive elements for the Digital Twin SCADA interface.

Provides:
- HoverTooltip: Spawns a floating tooltip box near the cursor on mouse hover.
- EquipmentDetailPopup: A non-blocking popup window showing detailed, live-updating
  parameters for a specific equipment.
"""

import tkinter as tk
import tkinter.ttk as ttk
from typing import Callable, Any

from gui.theme import (
    BG_PRIMARY, BG_SECONDARY, BG_HEADER, BORDER, BORDER_LIGHT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    CLR_NORMAL, CLR_WARNING, CLR_CRITICAL, CLR_OFFLINE,
    FONT_LABEL_SM, FONT_MONO_SM, FONT_SUBTITLE, status_color
)

# ═════════════════════════════════════════════════════════════════════════════
#  HOVER TOOLTIP
# ═════════════════════════════════════════════════════════════════════════════

class HoverTooltip:
    """
    Creates a hover tooltip for a tkinter widget or canvas item.
    """
    def __init__(self, canvas: tk.Canvas, tag_or_id: str | int, text_func: Callable[[], str]):
        """
        canvas: The canvas containing the item.
        tag_or_id: The canvas tag or item ID to bind to.
        text_func: A function that returns the current text to display.
        """
        self.canvas = canvas
        self.tag_or_id = tag_or_id
        self.text_func = text_func
        self.tw = None
        
        self.canvas.tag_bind(self.tag_or_id, "<Enter>", self._enter)
        self.canvas.tag_bind(self.tag_or_id, "<Leave>", self._leave)
        self.canvas.tag_bind(self.tag_or_id, "<Motion>", self._motion)

    def _enter(self, event=None):
        self._schedule_id = self.canvas.after(300, self._show_tooltip, event)

    def _leave(self, event=None):
        if hasattr(self, '_schedule_id'):
            self.canvas.after_cancel(self._schedule_id)
        self._hide_tooltip()

    def _motion(self, event):
        # Update tooltip position if it's visible
        if self.tw:
            x, y = self.canvas.winfo_pointerxy()
            self.tw.wm_geometry(f"+{x + 15}+{y + 10}")

    def _show_tooltip(self, event):
        if self.tw:
            return
            
        x, y = self.canvas.winfo_pointerxy()
        text = self.text_func()
        if not text:
            return

        self.tw = tk.Toplevel(self.canvas)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry(f"+{x + 15}+{y + 10}")
        # Keep tooltip on top
        self.tw.attributes("-topmost", True)

        frame = tk.Frame(self.tw, bg=BG_HEADER, highlightbackground=BORDER_LIGHT, highlightthickness=1)
        frame.pack(ipadx=4, ipady=4)

        label = tk.Label(
            frame, text=text, justify="left",
            bg=BG_HEADER, fg=TEXT_PRIMARY, font=FONT_MONO_SM,
        )
        label.pack()

    def _hide_tooltip(self):
        if self.tw:
            self.tw.destroy()
            self.tw = None


# ═════════════════════════════════════════════════════════════════════════════
#  EQUIPMENT DETAIL POPUP
# ═════════════════════════════════════════════════════════════════════════════

class EquipmentDetailPopup(tk.Toplevel):
    """
    A persistent, non-blocking floating window displaying detailed live stats
    for a single piece of equipment with professional paneling.
    """

    @classmethod
    def get_or_create(cls, parent: tk.Widget, equip_id: str, equip_type: str, app_context=None) -> 'EquipmentDetailPopup':
        from gui.window_manager import WindowManager
        
        # Check if already registered and alive
        if WindowManager.focus_if_exists(equip_id):
            return WindowManager._windows[equip_id]
        
        inst = cls(parent, equip_id, equip_type, app_context)
        WindowManager.register(equip_id, inst)
        return inst

    def __init__(self, parent: tk.Widget, equip_id: str, equip_type: str, app_context=None):
        super().__init__(parent)
        self.equip_id = equip_id
        self.equip_type = equip_type
        self.app_context = app_context
        
        self.title(f"Equipment Info: {equip_id}")
        self.configure(bg=BG_PRIMARY)
        self.geometry("800x650")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        
        self._vars: dict[str, tk.StringVar] = {}
        self._build_ui()

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=BG_HEADER)
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"{self.equip_type.upper()} | {self.equip_id}", bg=BG_HEADER, fg=TEXT_PRIMARY, font=FONT_SUBTITLE).pack(side="left", padx=10, pady=10)
        
        body = tk.Frame(self, bg=BG_PRIMARY)
        body.pack(fill="both", expand=True, padx=10, pady=10)
        body.columnconfigure(0, weight=1, uniform="col")
        body.columnconfigure(1, weight=1, uniform="col")
        body.rowconfigure(0, weight=1, uniform="row")
        body.rowconfigure(1, weight=1, uniform="row")

        # 1. Equipment Information
        self.info_f = tk.LabelFrame(body, text="Equipment Information", bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM)
        self.info_f.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # 2. Live Sensor Values
        self.sensor_f = tk.LabelFrame(body, text="Live Sensor Values", bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM)
        self.sensor_f.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # 3. AI Summary
        self.ai_f = tk.LabelFrame(body, text="AI Summary", bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM)
        self.ai_f.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # 4. Mini History Panel
        self.hist_f = tk.LabelFrame(body, text="Recent History", bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM)
        self.hist_f.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        
        self.txt_history = tk.Text(self.hist_f, bg=BG_PRIMARY, fg=TEXT_PRIMARY, font=FONT_MONO_SM, height=6, width=30, wrap="word", relief="flat")
        self.txt_history.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 5. Quick Actions
        actions_f = tk.Frame(self, bg=BG_HEADER)
        actions_f.pack(fill="x")
        
        tk.Button(actions_f, text="Open Historian", bg="#3b82f6", fg="white", relief="flat", command=lambda: self._trigger_action("trends")).pack(side="left", padx=5, pady=10)
        tk.Button(actions_f, text="Alarm History", bg="#ef4444", fg="white", relief="flat", command=lambda: self._trigger_action("alarms")).pack(side="left", padx=5, pady=10)
        tk.Button(actions_f, text="AI Timeline", bg="#8b5cf6", fg="white", relief="flat", command=lambda: self._trigger_action("ai_timeline")).pack(side="left", padx=5, pady=10)
        tk.Button(actions_f, text="Export Info", bg="#10b981", fg="white", relief="flat", command=self._export_info).pack(side="right", padx=10, pady=10)

    def _trigger_action(self, panel_name):
        if self.app_context:
            self.app_context._switch_panel(panel_name)
            
    def _export_info(self):
        import tkinter.filedialog as fd
        import datetime
        path = fd.asksaveasfilename(defaultextension=".txt", initialfile=f"{self.equip_id}_report_{datetime.datetime.now().strftime('%Y%m%d')}.txt")
        if not path: return
        try:
            with open(path, "w") as f:
                f.write(f"--- Equipment Report: {self.equip_id} ---\n\n")
                for k, v in self._vars.items():
                    k_clean = k.split("_", 1)[-1]
                    f.write(f"{k_clean}: {v.get()}\n")
            import tkinter.messagebox as mb
            mb.showinfo("Export Success", f"Information exported to {path}")
        except Exception as e:
            import tkinter.messagebox as mb
            mb.showerror("Export Error", str(e))

    def update_from_twin(self, eq):
        # 1. Equipment Information
        info_data = {
            "Name": eq.name,
            "ID": eq.id,
            "Type": eq.type,
            "Status": eq.status,
            "Running Hours": f"{eq.operating_hours:.1f} h",
            "Health Score": f"{eq.health_score:.1f} %",
            "Alarm Status": "CRITICAL" if eq.alarms else "NORMAL",
            "Current AI Risk": f"{eq.failure_risk:.1f} %",
            "Last Maintenance": getattr(eq, 'last_maintenance_date', 'Unknown'),
            "Next Planned Maint": getattr(eq, 'next_planned_maintenance', 'Unknown')
        }
        self._render_dict_to_frame(info_data, self.info_f, "info")
        
        # 2. Live Sensor Values
        sensor_data = {}
        if eq.motor_current > 0: sensor_data["Motor Current"] = f"{eq.motor_current:.1f} A"
        if eq.power_consumption > 0: sensor_data["Power Consumed"] = f"{eq.power_consumption:.1f} kW"
        for k, v in eq.sensors.items():
            if k in ["Operating Hours", "Motor Current (A)", "Power (kW)"]: continue
            sensor_data[k] = f"{v:.2f}" if isinstance(v, float) else str(v)
        if not sensor_data:
            sensor_data["Sensors"] = "No sensors attached"
        self._render_dict_to_frame(sensor_data, self.sensor_f, "sensor")
        
        # 3. AI Summary
        ai_data = {
            "Failure Probability": f"{eq.failure_risk:.1f} %",
            "Prediction Confidence": f"{eq.ai_confidence:.1f} %",
            "Maintenance Rec": eq.ai_recommendation,
            "Plant Status": eq.status
        }
        self._render_dict_to_frame(ai_data, self.ai_f, "ai")
        
        # 4. Mini History Panel
        self.txt_history.config(state="normal")
        self.txt_history.delete("1.0", "end")
        
        history_lines = []
        if eq.alarms:
            history_lines.append(f"ACTIVE ALARMS:\n- " + "\n- ".join(eq.alarms))
            
        if self.app_context and hasattr(self.app_context, '_decision_timeline'):
            # Fetch recent AI predictions
            tl = self.app_context._decision_timeline.get_timeline()
            if tl:
                latest = tl[-1]
                history_lines.append(f"\nLATEST AI DECISION ({latest['timestamp']}):\n{latest.get('reason_summary', '')}")
                
        if not history_lines:
            history_lines.append("No recent significant events or active alarms.")
            
        self.txt_history.insert("1.0", "\n".join(history_lines))
        self.txt_history.config(state="disabled")

    def _render_dict_to_frame(self, data_dict, frame, prefix):
        for i, (key, val) in enumerate(data_dict.items()):
            var_key = f"{prefix}_{key}"
            if var_key not in self._vars:
                self._vars[var_key] = tk.StringVar(value=str(val))
                lbl_key = tk.Label(frame, text=key, bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM, anchor="w", wraplength=140)
                lbl_key.grid(row=i, column=0, sticky="w", padx=(5, 10), pady=2)
                
                lbl_val = tk.Label(frame, textvariable=self._vars[var_key], bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_SM, anchor="w", wraplength=200, justify="left")
                lbl_val.grid(row=i, column=1, sticky="w", pady=2)
                
                if "status" in key.lower() or "health" in key.lower() or "risk" in key.lower() or "alarm" in key.lower():
                    self._update_color(lbl_val, str(val))
                    lbl_val._is_status = True
                else:
                    lbl_val._is_status = False
            else:
                self._vars[var_key].set(str(val))
                
        for child in frame.winfo_children():
            if isinstance(child, tk.Label) and getattr(child, '_is_status', False):
                self._update_color(child, child.cget("text"))

    def _update_color(self, label: tk.Label, text: str):
        text_upper = text.upper()
        if "CRIT" in text_upper or "FAULT" in text_upper or "CLOSED" in text_upper or "HIGH" in text_upper:
            label.config(fg=CLR_CRITICAL)
        elif "WARN" in text_upper or "THROTTLE" in text_upper or "MEDIUM" in text_upper:
            label.config(fg=CLR_WARNING)
        elif "OFF" in text_upper:
            label.config(fg=CLR_OFFLINE)
        else:
            label.config(fg=CLR_NORMAL)
