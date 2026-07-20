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
        self.resizable(False, False)
        
        self._build_ui()
        
        # Ensure it fits its contents and center it on the parent
        self.update_idletasks()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        
        # Provide a minimum width for a professional look
        if w < 450: w = 450
        
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_x()
        py = parent.winfo_y()
        
        # If parent is hidden or very small, center on screen instead
        if pw < 100 or ph < 100:
            pw = self.winfo_screenwidth()
            ph = self.winfo_screenheight()
            px = 0
            py = 0
            
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        self.focus_set()
        
        # Intercept close window event to exit application
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=BG_HEADER)
        hdr.pack(fill="x")
        tk.Label(
            hdr, text="ENTERPRISE SCADA LOGIN", bg=BG_HEADER, fg=TEXT_PRIMARY,
            font=FONT_TITLE, anchor="center"
        ).pack(fill="both", expand=True, pady=15)
        
        body = tk.Frame(self, bg=BG_PRIMARY, padx=40, pady=30)
        body.pack(fill="both", expand=True)
        
        # Username
        tk.Label(body, text="Username", bg=BG_PRIMARY, fg=TEXT_SECONDARY, font=FONT_LABEL).pack(anchor="w", pady=(0, 6))
        self.ent_username = tk.Entry(body, bg=BG_SECONDARY, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY, relief="flat", highlightbackground=BORDER, highlightthickness=1, font=FONT_LABEL)
        self.ent_username.pack(fill="x", pady=(0, 20), ipady=6)
        self.ent_username.focus_set()
        
        # Password
        tk.Label(body, text="Password", bg=BG_PRIMARY, fg=TEXT_SECONDARY, font=FONT_LABEL).pack(anchor="w", pady=(0, 6))
        self.ent_password = tk.Entry(body, show="*", bg=BG_SECONDARY, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY, relief="flat", highlightbackground=BORDER, highlightthickness=1, font=FONT_LABEL)
        self.ent_password.pack(fill="x", pady=(0, 20), ipady=6)
        
        # Error Label
        self.lbl_error = tk.Label(body, text="", bg=BG_PRIMARY, fg=CLR_CRITICAL, font=FONT_LABEL_SM, wraplength=380)
        self.lbl_error.pack(fill="x", pady=(0, 20))
        
        # Buttons Container (forces placement at bottom)
        btn_container = tk.Frame(body, bg=BG_PRIMARY)
        btn_container.pack(side="bottom", fill="x", pady=(10, 0))
        
        # Center the buttons
        btn_frame = tk.Frame(btn_container, bg=BG_PRIMARY)
        btn_frame.pack(anchor="center")
        
        # Submit Button
        btn_login = tk.Button(btn_frame, text="Login", bg="#10b981", fg="white", font=FONT_LABEL, relief="flat", cursor="hand2", command=self._login, width=14)
        btn_login.pack(side="left", padx=10, ipady=6)
        
        # Cancel Button
        btn_cancel = tk.Button(btn_frame, text="Cancel", bg="#4b5563", fg="white", font=FONT_LABEL, relief="flat", cursor="hand2", command=self._on_close, width=14)
        btn_cancel.pack(side="left", padx=10, ipady=6)
        
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
