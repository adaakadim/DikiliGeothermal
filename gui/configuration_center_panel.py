import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import csv
from pathlib import Path
import json
import yaml
import logging

from core.configuration import config
from gui.theme import (
    BG_PRIMARY, BG_SECONDARY, BG_TERTIARY, BORDER, 
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    FONT_TITLE, FONT_SUBTITLE, FONT_LABEL, FONT_MONO_SM,
    CLR_INFO, CLR_WARNING, CLR_CRITICAL, CLR_NORMAL
)

logger = logging.getLogger(__name__)

# Define schema for the UI
CONFIG_SCHEMA = {
    "Simulation": [
        {"key": "app.interval_ms", "label": "Tick Rate (ms)", "type": "int", "min": 100, "max": 5000},
        {"key": "simulation.noise_level", "label": "Sensor Noise Level", "type": "float", "min": 0.0, "max": 5.0},
        {"key": "simulation.base_temp", "label": "Base Temperature (°C)", "type": "float", "min": 50.0, "max": 150.0},
    ],
    "AI": [
        {"key": "ai.random_forest.n_estimators", "label": "RF Estimators", "type": "int", "min": 10, "max": 500},
        {"key": "ai.shap.background_samples", "label": "SHAP BG Samples", "type": "int", "min": 50, "max": 1000},
        {"key": "ai.rul.confidence_threshold", "label": "RUL Confidence Threshold (%)", "type": "float", "min": 50.0, "max": 100.0},
    ],
    "Historian": [
        {"key": "performance.historian.batch_size", "label": "Write Batch Size", "type": "int", "min": 1, "max": 5000},
        {"key": "performance.historian.flush_interval_s", "label": "Flush Interval (s)", "type": "float", "min": 1.0, "max": 60.0},
    ],
    "Alarms": [
        {"key": "alarms.limits.temp_high", "label": "Temp High Warn (°C)", "type": "float", "min": 80.0, "max": 110.0},
        {"key": "alarms.limits.pres_high", "label": "Pressure High Warn (bar)", "type": "float", "min": 5.0, "max": 15.0},
    ],
    "Dashboard": [
        {"key": "ui.refresh_rate_ms", "label": "UI Refresh Rate (ms)", "type": "int", "min": 500, "max": 5000},
        {"key": "ui.theme", "label": "Theme (dark/light)", "type": "str"},
    ],
    "Maintenance": [
        {"key": "maintenance.pm_interval_days", "label": "Default PM Interval (days)", "type": "int", "min": 30, "max": 365},
        {"key": "maintenance.alert_threshold", "label": "Health Alert Threshold (%)", "type": "float", "min": 10.0, "max": 90.0},
    ],
    "Engineering Assets": [
        {"key": "assets.hx_eff_target", "label": "HX Efficiency Target (%)", "type": "float", "min": 70.0, "max": 100.0},
        {"key": "assets.pump_max_power_kw", "label": "Pump Max Power (kW)", "type": "float", "min": 100.0, "max": 2000.0},
    ]
}

class ConfigurationCenterPanel(tk.Frame):
    def __init__(self, parent: tk.Widget):
        super().__init__(parent, bg=BG_PRIMARY)
        self.pack_propagate(False)
        
        self._edit_mode = False
        self._current_category = "Simulation"
        self._entry_widgets = {}  # key -> widget
        
        self._build_ui()
        self._load_category("Simulation")
        
    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=BG_SECONDARY, height=60)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        
        title = tk.Label(header, text="⚙️ Engineering Configuration Center", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_TITLE)
        title.pack(side="left", padx=20, pady=15)
        
        # Mode Toggle
        self.btn_edit = tk.Button(header, text="Enable Edit Mode", bg="#334155", fg="#f8fafc", bd=0, padx=15, font=FONT_LABEL, command=self._toggle_mode)
        self.btn_edit.pack(side="right", padx=20, pady=15)
        
        # Main Layout
        content = tk.Frame(self, bg=BG_PRIMARY)
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Sidebar
        sidebar = tk.Frame(content, bg=BG_SECONDARY, width=220)
        sidebar.pack(side="left", fill="y", padx=(0, 20))
        sidebar.pack_propagate(False)
        
        tk.Label(sidebar, text="CATEGORIES", bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=("Segoe UI", 10, "bold")).pack(pady=(15, 5), padx=10, anchor="w")
        
        self._category_buttons = {}
        for cat in CONFIG_SCHEMA.keys():
            btn = tk.Button(sidebar, text=cat, bg=BG_SECONDARY, fg=TEXT_PRIMARY, bd=0, anchor="w", padx=20, pady=8, font=FONT_LABEL, command=lambda c=cat: self._load_category(c))
            btn.pack(fill="x")
            self._category_buttons[cat] = btn
            
        # Form Area
        self.form_frame = tk.Frame(content, bg=BG_TERTIARY, highlightbackground=BORDER, highlightthickness=1)
        self.form_frame.pack(side="left", fill="both", expand=True)
        
        # Form Header
        self.lbl_category_title = tk.Label(self.form_frame, text="Category", bg=BG_TERTIARY, fg=TEXT_PRIMARY, font=FONT_SUBTITLE)
        self.lbl_category_title.grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(20, 10))
        
        # Container for dynamic fields
        self.fields_frame = tk.Frame(self.form_frame, bg=BG_TERTIARY)
        self.fields_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=20)
        self.form_frame.rowconfigure(1, weight=1)
        self.form_frame.columnconfigure(1, weight=1)
        
        # Actions Footer
        actions = tk.Frame(self.form_frame, bg=BG_SECONDARY, height=60, highlightbackground=BORDER, highlightthickness=1)
        actions.grid(row=2, column=0, columnspan=2, sticky="ew")
        actions.pack_propagate(False)
        
        self.btn_save = tk.Button(actions, text="Validate & Save", bg=CLR_INFO, fg="#ffffff", bd=0, padx=15, font=FONT_LABEL, command=self._save_config)
        self.btn_save.pack(side="right", padx=20, pady=15)
        
        self.btn_defaults = tk.Button(actions, text="Restore Defaults", bg="#475569", fg="#f8fafc", bd=0, padx=15, font=FONT_LABEL, command=self._restore_defaults)
        self.btn_defaults.pack(side="right", padx=10, pady=15)
        
        self.btn_export = tk.Button(actions, text="Export...", bg="#334155", fg="#f8fafc", bd=0, padx=15, font=FONT_LABEL, command=self._export_config)
        self.btn_export.pack(side="left", padx=20, pady=15)
        
        self.btn_import = tk.Button(actions, text="Import...", bg="#334155", fg="#f8fafc", bd=0, padx=15, font=FONT_LABEL, command=self._import_config)
        self.btn_import.pack(side="left", padx=10, pady=15)

    def _toggle_mode(self):
        self._edit_mode = not self._edit_mode
        if self._edit_mode:
            self.btn_edit.config(text="View Mode", bg="#475569")
        else:
            self.btn_edit.config(text="Enable Edit Mode", bg="#334155")
            
        self._load_category(self._current_category)

    def _load_category(self, category: str):
        self._current_category = category
        self.lbl_category_title.config(text=f"{category} Configuration")
        
        for cat, btn in self._category_buttons.items():
            if cat == category:
                btn.config(bg="#3b82f6", fg="#ffffff")
            else:
                btn.config(bg=BG_SECONDARY, fg=TEXT_PRIMARY)
                
        # Clear existing fields
        for widget in self.fields_frame.winfo_children():
            widget.destroy()
            
        self._entry_widgets.clear()
        
        schema = CONFIG_SCHEMA.get(category, [])
        for i, item in enumerate(schema):
            key = item["key"]
            lbl = tk.Label(self.fields_frame, text=item["label"], bg=BG_TERTIARY, fg=TEXT_SECONDARY, font=FONT_LABEL)
            lbl.grid(row=i, column=0, sticky="w", pady=10, padx=(0, 20))
            
            # Fetch current value, falling back to a sensible default if not found
            current_val = config.get(key)
            if current_val is None:
                if item["type"] == "int": current_val = 0
                elif item["type"] == "float": current_val = 0.0
                else: current_val = ""
            
            entry_var = tk.StringVar(value=str(current_val))
            entry = ttk.Entry(self.fields_frame, textvariable=entry_var, font=FONT_MONO_SM, width=30)
            entry.grid(row=i, column=1, sticky="w", pady=10)
            
            if not self._edit_mode:
                entry.state(["readonly"])
                
            self._entry_widgets[key] = {
                "var": entry_var,
                "type": item["type"],
                "min": item.get("min"),
                "max": item.get("max"),
                "label": item["label"]
            }
            
            # Show limits as hint
            if "min" in item and "max" in item:
                hint = tk.Label(self.fields_frame, text=f"({item['min']} - {item['max']})", bg=BG_TERTIARY, fg=TEXT_MUTED, font=("Segoe UI", 8))
                hint.grid(row=i, column=2, sticky="w", padx=10)

        # Update button states
        state = "normal" if self._edit_mode else "disabled"
        self.btn_save.config(state=state)
        self.btn_defaults.config(state=state)
        self.btn_import.config(state=state)

    def _save_config(self):
        if not self._edit_mode: return
        
        changes = []
        errors = []
        
        # Validation
        for key, data in self._entry_widgets.items():
            raw_val = data["var"].get()
            t = data["type"]
            val = None
            
            try:
                if t == "int": val = int(raw_val)
                elif t == "float": val = float(raw_val)
                else: val = str(raw_val)
                
                if data["min"] is not None and val < data["min"]:
                    errors.append(f"{data['label']} must be >= {data['min']}")
                if data["max"] is not None and val > data["max"]:
                    errors.append(f"{data['label']} must be <= {data['max']}")
            except ValueError:
                errors.append(f"{data['label']} must be of type {t}")
                continue
                
            old_val = config.get(key)
            if str(old_val) != str(val):
                changes.append((key, old_val, val))
                
        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors))
            return
            
        if not changes:
            messagebox.showinfo("No Changes", "No configuration values were modified.")
            return
            
        # Apply changes
        for key, old_val, new_val in changes:
            config.set(key, new_val)
            
        # Log to Audit file
        self._log_audit(changes)
        
        config.save()
        messagebox.showinfo("Success", f"Successfully updated and saved {len(changes)} parameter(s).")
        
        # Ensure we're showing the newly applied formatted versions
        self._load_category(self._current_category)

    def _log_audit(self, changes):
        log_path = Path("data/config_audit.csv")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        write_header = not log_path.exists()
        
        try:
            with open(log_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if write_header:
                    writer.writerow(["Timestamp", "User", "Key", "Old Value", "New Value"])
                    
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                user = "Admin" # Placeholder for auth module integration
                
                for key, old_val, new_val in changes:
                    writer.writerow([ts, user, key, str(old_val), str(new_val)])
                    logger.info(f"Config Audit: [{user}] changed {key} from '{old_val}' to '{new_val}'")
        except Exception as e:
            logger.error(f"Failed to write to audit log: {e}")

    def _restore_defaults(self):
        if messagebox.askyesno("Confirm Restore", "Restore all settings in this category to system defaults?"):
            try:
                # Load default.yaml manually
                config_dir = Path("config")
                default_path = config_dir / "default.yaml"
                if default_path.exists():
                    with open(default_path, "r", encoding="utf-8") as f:
                        defaults = yaml.safe_load(f) or {}
                    
                    schema = CONFIG_SCHEMA.get(self._current_category, [])
                    restored_count = 0
                    for item in schema:
                        key = item["key"]
                        # Nested dict get
                        keys = key.split(".")
                        val = defaults
                        for k in keys:
                            if isinstance(val, dict) and k in val: val = val[k]
                            else: val = None; break
                        
                        if val is not None:
                            config.set(key, val)
                            restored_count += 1
                            
                    config.save()
                    self._log_audit([("RESTORE_DEFAULTS", "N/A", self._current_category)])
                    self._load_category(self._current_category)
                    messagebox.showinfo("Defaults Restored", f"Restored {restored_count} parameters.")
                else:
                    messagebox.showerror("Error", "default.yaml not found.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _export_config(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json"), ("YAML files", "*.yaml")], title="Export Configuration")
        if not path: return
        
        try:
            export_data = config._config
            with open(path, "w", encoding="utf-8") as f:
                if path.endswith(".json"):
                    json.dump(export_data, f, indent=4)
                else:
                    yaml.dump(export_data, f)
            messagebox.showinfo("Export Success", f"Configuration exported to {path}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

    def _import_config(self):
        if not self._edit_mode: return
        
        path = filedialog.askopenfilename(filetypes=[("Configuration Files", "*.json *.yaml")], title="Import Configuration")
        if not path: return
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                if path.endswith(".json"):
                    imported_data = json.load(f)
                else:
                    imported_data = yaml.safe_load(f)
                    
            config._merge(config._config, imported_data)
            config.save()
            
            # Simple audit log for bulk import
            self._log_audit([("BULK_IMPORT", "N/A", path)])
            
            self._load_category(self._current_category)
            messagebox.showinfo("Import Success", "Configuration imported and saved.")
        except Exception as e:
            messagebox.showerror("Import Failed", str(e))
