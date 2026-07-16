import tkinter as tk
from tkinter import ttk
from typing import Dict, Any
from gui.theme import FONT_TITLE, FONT_SUBTITLE, FONT_LABEL, BG_SECONDARY

class AIExplainabilityPanel(ttk.Frame):
    def __init__(self, parent: ttk.Frame):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 1. Header
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        self.lbl_title = ttk.Label(header_frame, text="AI Explainability: SELECT EQUIPMENT", font=FONT_TITLE)
        self.lbl_title.pack(side=tk.LEFT)
        
        self.lbl_risk = ttk.Label(header_frame, text="Risk: --%", font=FONT_SUBTITLE, foreground="#94a3b8")
        self.lbl_risk.pack(side=tk.RIGHT, padx=10)
        
        self.lbl_conf = ttk.Label(header_frame, text="Confidence: --%", font=FONT_SUBTITLE, foreground="#94a3b8")
        self.lbl_conf.pack(side=tk.RIGHT, padx=10)
        
        content = ttk.Frame(self)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Define layout containers
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        bot_frame = ttk.Frame(self)
        bot_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # 2. Root Cause Chain
        rc_frame = ttk.LabelFrame(main_frame, text="Root Cause Chain", padding=10)
        rc_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        self.lbl_root_cause = ttk.Label(rc_frame, text="Waiting for explanation...", font=FONT_LABEL, wraplength=400)
        self.lbl_root_cause.pack(anchor="w", fill=tk.X)
        
        # 3. Main Contributing Variables
        var_frame = ttk.LabelFrame(main_frame, text="Main Contributing Variables", padding=10)
        var_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree_vars = ttk.Treeview(var_frame, columns=("variable", "impact"), show="headings", height=6)
        self.tree_vars.heading("variable", text="Variable")
        self.tree_vars.heading("impact", text="Relative Impact")
        self.tree_vars.column("variable", width=250)
        self.tree_vars.column("impact", width=100, anchor=tk.CENTER)
        self.tree_vars.pack(fill=tk.BOTH, expand=True)
        
        # 4. Engineering Explanation
        exp_frame = ttk.LabelFrame(bot_frame, text="Engineering Explanation", padding=10)
        exp_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        self.txt_explain = tk.Text(exp_frame, height=8, wrap=tk.WORD, font=FONT_LABEL, 
                                     bg="#0f172a", fg="#f8fafc",
                                     state=tk.DISABLED)
        self.txt_explain.pack(fill=tk.BOTH, expand=True)
        
        # 5. Recommended Actions
        rec_frame = ttk.LabelFrame(bot_frame, text="Recommended Actions", padding=10)
        rec_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.txt_actions = tk.Text(rec_frame, height=6, wrap=tk.WORD, font=FONT_LABEL, 
                                     bg="#0f172a", fg="#f8fafc",
                                     state=tk.DISABLED)
        self.txt_actions.pack(fill=tk.BOTH, expand=True)

    def _update_text(self, widget: tk.Text, text_content: str):
        widget.config(state=tk.NORMAL)
        widget.delete(1.0, tk.END)
        widget.insert(tk.END, text_content)
        widget.config(state=tk.DISABLED)

    def update_explanation(self, target_id: str, risk: float, conf: float, explanation: Dict[str, Any]):
        """Populates the panel with explanation data."""
        self.lbl_title.config(text=f"AI Explainability: {target_id.upper()}")
        self.lbl_risk.config(text=f"Risk: {risk:.1f}%")
        self.lbl_conf.config(text=f"Confidence: {conf:.1f}%")
        
        # Root Cause
        chain = explanation.get("root_cause_chain", [])
        if chain:
            self.lbl_root_cause.config(text=" ➔ ".join(chain))
        else:
            self.lbl_root_cause.config(text="No root cause chain available.")
            
        # Variables
        for item in self.tree_vars.get_children():
            self.tree_vars.delete(item)
            
        ranked = explanation.get("ranked_variables", [])
        for var, impact in ranked:
            self.tree_vars.insert("", tk.END, values=(var, f"{impact:.1f}"))
            
        # Text blocks
        eng_exp = explanation.get("engineering_explanation", "No explanation provided.")
        self._update_text(self.txt_explain, eng_exp)
        
        actions = explanation.get("recommended_actions", [])
        actions_str = "\n".join(f"• {a}" for a in actions) if actions else "• None"
        self._update_text(self.txt_actions, actions_str)
