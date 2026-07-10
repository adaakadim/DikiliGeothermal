import tkinter as tk
import tkinter.ttk as ttk
from analytics.ai.decision_analyzer import DecisionAnalyzer
from gui.theme import (
    BG_PRIMARY, BG_SECONDARY, BG_HEADER, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY,
    CLR_NORMAL, CLR_WARNING, CLR_CRITICAL,
    FONT_LABEL_SM, FONT_MONO_SM, FONT_SUBTITLE
)

class DecisionComparisonDialog(tk.Toplevel):
    def __init__(self, parent, event1, event2):
        super().__init__(parent)
        self.title("Decision Comparison")
        self.geometry("800x600")
        self.configure(bg=BG_PRIMARY)
        
        # Sort chronologically
        try:
            t1 = event1.get("timestamp", "")
            t2 = event2.get("timestamp", "")
            if t1 > t2:
                event1, event2 = event2, event1
        except Exception:
            pass
            
        pred1 = event1.get("prediction", {})
        pred2 = event2.get("prediction", {})
        feat1 = event1.get("raw_features", {})
        feat2 = event2.get("raw_features", {})
        
        # Compare
        self.comparison = DecisionAnalyzer.compare_decisions(pred1, pred2, feat1, feat2)
        
        self._build_ui(event1, event2)
        
    def _build_ui(self, ev1, ev2):
        hdr = tk.Frame(self, bg=BG_HEADER)
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"COMPARING PREDICTIONS", bg=BG_HEADER, fg="#0ea5e9", font=FONT_SUBTITLE).pack(pady=10)
        
        # Header info
        info_f = tk.Frame(self, bg=BG_SECONDARY)
        info_f.pack(fill="x", padx=10, pady=5)
        
        t1 = ev1.get("timestamp", "")
        t2 = ev2.get("timestamp", "")
        tk.Label(info_f, text=f"Previous: {t1}  ➔  Current: {t2}", bg=BG_SECONDARY, fg=TEXT_PRIMARY, font=FONT_MONO_SM).pack(pady=5)
        
        # Deltas
        delta_f = tk.Frame(self, bg=BG_PRIMARY)
        delta_f.pack(fill="x", padx=10, pady=5)
        
        deltas = self.comparison.get("deltas", {})
        r_d = deltas.get("risk", 0.0)
        h_d = deltas.get("health", 0.0)
        c_d = deltas.get("confidence", 0.0)
        
        tk.Label(delta_f, text=f"Risk Delta: {r_d:+.2f}%", bg=BG_PRIMARY, fg=CLR_CRITICAL if r_d > 0 else CLR_NORMAL, font=FONT_MONO_SM).pack(side="left", padx=20)
        tk.Label(delta_f, text=f"Health Delta: {h_d:+.2f}%", bg=BG_PRIMARY, fg=CLR_NORMAL if h_d > 0 else CLR_WARNING, font=FONT_MONO_SM).pack(side="left", padx=20)
        tk.Label(delta_f, text=f"Conf Delta: {c_d:+.2f}%", bg=BG_PRIMARY, fg=TEXT_PRIMARY, font=FONT_MONO_SM).pack(side="left", padx=20)
        
        # Reason Summary
        rs_f = tk.LabelFrame(self, text="Engineering Reason Summary", bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM)
        rs_f.pack(fill="x", padx=10, pady=10)
        
        txt = tk.Text(rs_f, height=3, bg=BG_PRIMARY, fg=TEXT_PRIMARY, font=FONT_MONO_SM, wrap="word")
        txt.pack(fill="both", expand=True, padx=5, pady=5)
        txt.insert("1.0", self.comparison.get("reason_summary", ""))
        txt.config(state="disabled")
        
        # Sensors
        s_f = tk.LabelFrame(self, text="Sensor Changes", bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL_SM)
        s_f.pack(fill="both", expand=True, padx=10, pady=5)
        
        cols = ("feat", "old", "new", "diff", "pct")
        tree = ttk.Treeview(s_f, columns=cols, show="headings")
        tree.heading("feat", text="Feature")
        tree.heading("old", text="Old Val")
        tree.heading("new", text="New Val")
        tree.heading("diff", text="Diff")
        tree.heading("pct", text="Change %")
        tree.column("feat", width=250)
        tree.column("old", width=100, anchor="e")
        tree.column("new", width=100, anchor="e")
        tree.column("diff", width=100, anchor="e")
        tree.column("pct", width=100, anchor="e")
        
        tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        for ch in self.comparison.get("sensor_changes", []):
            tree.insert("", "end", values=(
                ch.get("feature"),
                ch.get("old"),
                ch.get("new"),
                ch.get("diff"),
                ch.get("pct")
            ))
            
        btn_close = tk.Button(self, text="Close", command=self.destroy, bg="#333", fg="white", relief="flat")
        btn_close.pack(pady=10)
