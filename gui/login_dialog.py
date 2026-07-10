"""
gui/login_dialog.py
===================
Enterprise Login Dialog (Toplevel) for DikiliGeothermal HMI.
"""

import sys
import tkinter as tk
from gui.theme import (
    BG_PRIMARY, BG_SECONDARY, BG_HEADER, BORDER, TEXT_PRIMARY, TEXT_SECONDARY,
    CLR_CRITICAL, FONT_TITLE, FONT_LABEL, FONT_LABEL_SM
)
from security.authentication import AuthenticationService

class LoginDialog(tk.Toplevel):
    def __init__(self, parent, on_success_callback):
        super().__init__(parent)
        self.parent = parent
        self.on_success = on_success_callback
        self.auth_service = AuthenticationService()
        
        self.title("SCADA System Login")
        self.configure(bg=BG_PRIMARY)
        self.geometry("400x300")
        self.resizable(False, False)
        
        # Center the dialog on the parent window
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_x()
        py = parent.winfo_y()
        x = px + (pw - 400) // 2
        y = py + (ph - 300) // 2
        self.geometry(f"400x300+{x}+{y}")
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        self.focus_set()
        
        # Intercept close window event to exit application
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        self._build_ui()
        
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=BG_HEADER, height=50)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(
            hdr, text="ENTERPRISE SCADA LOGIN", bg=BG_HEADER, fg=TEXT_PRIMARY,
            font=FONT_TITLE, anchor="center"
        ).pack(fill="both", expand=True)
        
        body = tk.Frame(self, bg=BG_PRIMARY, padx=30, pady=20)
        body.pack(fill="both", expand=True)
        
        # Username
        tk.Label(body, text="Username", bg=BG_PRIMARY, fg=TEXT_SECONDARY, font=FONT_LABEL).pack(anchor="w", pady=(0, 2))
        self.ent_username = tk.Entry(body, bg=BG_SECONDARY, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY, relief="flat", highlightbackground=BORDER, highlightthickness=1, font=FONT_LABEL)
        self.ent_username.pack(fill="x", pady=(0, 10))
        self.ent_username.focus_set()
        
        # Password
        tk.Label(body, text="Password", bg=BG_PRIMARY, fg=TEXT_SECONDARY, font=FONT_LABEL).pack(anchor="w", pady=(0, 2))
        self.ent_password = tk.Entry(body, show="*", bg=BG_SECONDARY, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY, relief="flat", highlightbackground=BORDER, highlightthickness=1, font=FONT_LABEL)
        self.ent_password.pack(fill="x", pady=(0, 15))
        
        # Error Label
        self.lbl_error = tk.Label(body, text="", bg=BG_PRIMARY, fg=CLR_CRITICAL, font=FONT_LABEL_SM, wraplength=340)
        self.lbl_error.pack(fill="x", pady=(0, 5))
        
        # Buttons Frame
        btn_frame = tk.Frame(body, bg=BG_PRIMARY)
        btn_frame.pack(fill="x")
        
        # Submit Button
        btn_login = tk.Button(btn_frame, text="Login", bg="#10b981", fg="white", font=FONT_LABEL, relief="flat", cursor="hand2", command=self._login, width=12)
        btn_login.pack(side="right", padx=(5, 0))
        
        # Cancel Button
        btn_cancel = tk.Button(btn_frame, text="Cancel", bg="#4b5563", fg="white", font=FONT_LABEL, relief="flat", cursor="hand2", command=self._on_close, width=12)
        btn_cancel.pack(side="right")
        
        # Bind Enter key to submit
        self.bind("<Return>", lambda e: self._login())

    def _login(self):
        username = self.ent_username.get().strip()
        password = self.ent_password.get()
        
        if not username or not password:
            self.lbl_error.config(text="Please fill in all fields.")
            return
            
        session = self.auth_service.authenticate(username, password)
        if session:
            # Login successful
            self.grab_release()
            self.destroy()
            self.on_success(username, session)
        else:
            # Check if user got locked out
            if username in self.auth_service._locked_users:
                self.lbl_error.config(text="Account locked due to too many failed attempts.")
            else:
                self.lbl_error.config(text="Invalid username or password.")

    def _on_close(self):
        self.grab_release()
        self.destroy()
        self.parent.destroy()
        sys.exit(0)
