import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as mb
from datetime import datetime, timedelta

from gui.theme import FONT_TITLE, FONT_LABEL, FONT_LABEL_SM, BG_PRIMARY
from scada.enterprise_report_generator import EnterpriseReportGenerator

class ReportingCenterPanel(ttk.Frame):
    def __init__(self, parent: tk.Widget, generator: EnterpriseReportGenerator, on_generate_cb=None):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True)
        
        self.generator = generator
        self.on_generate_cb = on_generate_cb
        
        self.report_types = [
            "Daily Plant Report",
            "Weekly Plant Report",
            "Monthly Plant Report",
            "Maintenance Report",
            "Alarm Report",
            "Energy Report",
            "AI Performance Report",
            "Plant Performance Report"
        ]
        
        self.export_formats = ["PDF", "Excel (.xlsx)", "CSV"]
        
        self._build_ui()
        
    def _build_ui(self):
        # Header
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=20, pady=(20, 10))
        ttk.Label(header, text="ENTERPRISE REPORTING CENTER", font=FONT_TITLE).pack(side=tk.LEFT)
        
        # Main Container
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Left Panel (Controls)
        left_panel = ttk.LabelFrame(container, text="Report Configuration", padding=15)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        ttk.Label(left_panel, text="Report Type:", font=FONT_LABEL).pack(anchor="w", pady=(0, 5))
        self.cb_type = ttk.Combobox(left_panel, values=self.report_types, state="readonly", width=30)
        self.cb_type.set(self.report_types[0])
        self.cb_type.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(left_panel, text="Export Format:", font=FONT_LABEL).pack(anchor="w", pady=(0, 5))
        self.cb_format = ttk.Combobox(left_panel, values=self.export_formats, state="readonly", width=30)
        self.cb_format.set("PDF")
        self.cb_format.pack(fill=tk.X, pady=(0, 15))
        
        # Dates
        dates_frame = ttk.Frame(left_panel)
        dates_frame.pack(fill=tk.X, pady=(0, 15))
        
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        
        ttk.Label(dates_frame, text="Start Date (YYYY-MM-DD):", font=FONT_LABEL_SM).pack(anchor="w")
        self.ent_start = ttk.Entry(dates_frame)
        self.ent_start.insert(0, yesterday.strftime("%Y-%m-%d"))
        self.ent_start.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(dates_frame, text="End Date (YYYY-MM-DD):", font=FONT_LABEL_SM).pack(anchor="w")
        self.ent_end = ttk.Entry(dates_frame)
        self.ent_end.insert(0, now.strftime("%Y-%m-%d"))
        self.ent_end.pack(fill=tk.X)
        
        ttk.Label(left_panel, text="Operator Name:", font=FONT_LABEL).pack(anchor="w", pady=(0, 5))
        self.ent_operator = ttk.Entry(left_panel)
        self.ent_operator.insert(0, "Admin")
        self.ent_operator.pack(fill=tk.X, pady=(0, 20))
        
        self.btn_generate = ttk.Button(left_panel, text="📄 Generate Report", command=self._on_generate_clicked)
        self.btn_generate.pack(fill=tk.X, pady=(10, 0))
        
        # Right Panel (Logs / Preview)
        right_panel = ttk.LabelFrame(container, text="Generation Logs", padding=15)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.txt_logs = tk.Text(right_panel, bg="#1e293b", fg="#e2e8f0", font=("Consolas", 10), state=tk.DISABLED)
        self.txt_logs.pack(fill=tk.BOTH, expand=True)

    def _log(self, msg: str):
        self.txt_logs.config(state=tk.NORMAL)
        self.txt_logs.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.txt_logs.see(tk.END)
        self.txt_logs.config(state=tk.DISABLED)
        self.update_idletasks()

    def _on_generate_clicked(self):
        rt = self.cb_type.get()
        fmt = self.cb_format.get()
        op = self.ent_operator.get()
        ds = self.ent_start.get()
        de = self.ent_end.get()
        
        self._log(f"Starting generation for {rt} ({fmt})...")
        self._log("Gathering enterprise data...")
        
        # We delegate the actual data gathering to the main window through the callback
        if self.on_generate_cb:
            try:
                # Disable button
                self.btn_generate.config(state=tk.DISABLED)
                
                # Fetch data from main application layer
                data = self.on_generate_cb()
                
                self._log("Data aggregated successfully.")
                self._log(f"Compiling {fmt} document...")
                
                filepath = self.generator.generate_report(
                    report_type=rt,
                    export_format=fmt,
                    operator_name=op,
                    scenario_name=data.get("scenario", "NORMAL"),
                    date_range_start=ds,
                    date_range_end=de,
                    data=data
                )
                
                self._log(f"SUCCESS: Report saved to {filepath}")
                mb.showinfo("Report Generated", f"Report successfully saved to:\n{filepath}")
                
            except Exception as e:
                import traceback
                self._log(f"ERROR: {str(e)}")
                traceback.print_exc()
                mb.showerror("Generation Error", f"An error occurred while generating the report:\n{str(e)}")
            finally:
                self.btn_generate.config(state=tk.NORMAL)
        else:
            self._log("ERROR: No data provider callback configured.")
