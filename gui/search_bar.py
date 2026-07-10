import tkinter as tk
from tkinter import ttk
import logging
from gui.theme import BG_SECONDARY, BG_TERTIARY, BORDER, TEXT_PRIMARY, TEXT_SECONDARY, FONT_MONO_SM, FONT_LABEL

logger = logging.getLogger(__name__)

class EquipmentSearchBar(tk.Frame):
    def __init__(self, parent, facility_provider=None, on_select=None, **kwargs):
        super().__init__(parent, bg=BG_SECONDARY, highlightbackground=BORDER, highlightthickness=1, **kwargs)
        
        self.facility_provider = facility_provider
        self.on_select = on_select
        self._history = []
        
        # Search Icon (Magnifying Glass)
        tk.Label(self, text="🔍", bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=FONT_LABEL).pack(side="left", padx=(5, 0))
        
        self.entry_var = tk.StringVar()
        self.entry_var.trace_add("write", self._on_type)
        
        self.entry = tk.Entry(
            self, textvariable=self.entry_var, bg=BG_SECONDARY, fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY, font=FONT_LABEL, relief="flat", width=30
        )
        self.entry.pack(side="left", fill="both", expand=True, padx=5, pady=2)
        
        self.entry.bind("<FocusIn>", self._on_focus)
        self.entry.bind("<FocusOut>", self._on_unfocus)
        
        # Ensure clicking outside the search bar closes the dropdown
        # Bind to the top-level window to catch clicks anywhere
        self.winfo_toplevel().bind("<Button-1>", self._check_click_outside, add="+")
        
        self.entry.bind("<Down>", self._on_down_arrow)
        self.entry.bind("<Up>", self._on_up_arrow)
        self.entry.bind("<Escape>", self._on_escape)
        self.entry.bind("<Return>", self._on_return)
        
        # Dropdown window
        self.dropdown = None
        
        # Placeholder logic
        self._placeholder = "Search Equipment (e.g. P-101)..."
        self._put_placeholder()

    def _check_click_outside(self, event):
        # If the click is not inside the search bar or its dropdown, unfocus
        widget = event.widget
        if widget != self.entry and widget != getattr(self, 'listbox', None):
            self.focus_set() # Give focus back to the parent frame to trigger FocusOut on entry

    def _put_placeholder(self):
        if not self.entry.get():
            self.entry.insert(0, self._placeholder)
            self.entry.config(fg=TEXT_SECONDARY)

    def _remove_placeholder(self):
        if self.entry.get() == self._placeholder:
            self.entry.delete(0, "end")
            self.entry.config(fg=TEXT_PRIMARY)

    def _on_focus(self, event):
        self._remove_placeholder()
        self._show_dropdown()

    def _on_unfocus(self, event):
        if not self.entry.get():
            self._put_placeholder()
        # Delay hiding dropdown so clicks register
        self.after(500, self._hide_dropdown)

    def _on_type(self, *args):
        if self.entry.get() == self._placeholder:
            return
        logger.info("Search started: Entry typed")
        self._show_dropdown()

    def _show_dropdown(self):
        if not self.facility_provider:
            return
            
        term = self.entry.get().strip().lower()
        if term == self._placeholder.lower():
            term = ""

        facility = self.facility_provider()
        if not facility:
            return

        # Find matches
        matches = []
        if not term:
            # Show history if empty
            for h in reversed(self._history):
                matches.append(h)
        else:
            for eq_id, eq in facility.equipment.items():
                if term in eq_id.lower() or term in eq.name.lower() or term in eq.type.lower():
                    matches.append((eq_id, eq.name, eq.type))

        if not matches:
            logger.info("No matches found")
            self._hide_dropdown()
            return
            
        logger.info(f"Suggestions generated: {len(matches)} matches")

        if not self.dropdown:
            self.dropdown = tk.Toplevel(self)
            self.dropdown.wm_overrideredirect(True)
            self.dropdown.configure(bg=BG_TERTIARY, highlightbackground=BORDER, highlightthickness=1)
            
            self.listbox = tk.Listbox(
                self.dropdown, bg=BG_TERTIARY, fg=TEXT_PRIMARY, selectbackground="#374151",
                selectforeground="#60a5fa", font=FONT_MONO_SM, relief="flat", highlightthickness=0
            )
            self.listbox.pack(fill="both", expand=True)
            self.listbox.bind("<<ListboxSelect>>", self._on_listbox_select)
            self.listbox.bind("<Return>", self._on_listbox_select)

        # Position dropdown
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        w = self.winfo_width()
        
        h = min(150, len(matches) * 22)
        self.dropdown.geometry(f"{w}x{h}+{x}+{y}")
        self.dropdown.deiconify()
        self.dropdown.lift()
        self.dropdown.attributes("-topmost", True)

        # Populate listbox
        self.listbox.delete(0, "end")
        for match in matches[:10]: # Max 10 items
            if isinstance(match, tuple):
                self.listbox.insert("end", f"{match[0]} - {match[1]} ({match[2]})")
            else:
                self.listbox.insert("end", f"🕒 {match[0]} - {match[1]} ({match[2]})")

    def _hide_dropdown(self):
        if self.dropdown:
            self.dropdown.withdraw()

    def _on_escape(self, event):
        self._hide_dropdown()
        self.focus_set()

    def _on_down_arrow(self, event):
        if self.dropdown and self.dropdown.winfo_ismapped() and self.listbox.size() > 0:
            current = self.listbox.curselection()
            if not current:
                self.listbox.selection_set(0)
            else:
                idx = current[0]
                if idx < self.listbox.size() - 1:
                    self.listbox.selection_clear(idx)
                    self.listbox.selection_set(idx + 1)
            self.listbox.see(self.listbox.curselection()[0])
        return "break" # Prevent default behavior

    def _on_up_arrow(self, event):
        if self.dropdown and self.dropdown.winfo_ismapped() and self.listbox.size() > 0:
            current = self.listbox.curselection()
            if current:
                idx = current[0]
                if idx > 0:
                    self.listbox.selection_clear(idx)
                    self.listbox.selection_set(idx - 1)
                self.listbox.see(self.listbox.curselection()[0])
        return "break" # Prevent default behavior

    def _on_return(self, event):
        self._show_dropdown()
        if self.dropdown and self.dropdown.winfo_ismapped() and self.listbox.size() > 0:
            if not self.listbox.curselection():
                self.listbox.selection_set(0)
            self._on_listbox_select(None)

    def _on_listbox_select(self, event=None):
        logger.info(f"Suggestion clicked: Event={event}, type={getattr(event, 'type', 'None')}")
        
        # In ListboxSelect or Return, curselection is already updated
        current = self.listbox.curselection()
        if not current:
            # Fallback for mouse click if curselection is empty (rare but possible)
            if event and hasattr(event, 'y'):
                idx = self.listbox.nearest(event.y)
                if idx >= 0:
                    self.listbox.selection_set(idx)
                    current = (idx,)
            
        if not current:
            logger.warning("No index found during selection")
            return
            
        idx = current[0]
            
        val = self.listbox.get(idx)
        logger.info(f"Equipment selected: {val}")
        
        # Parse EQ ID from string "ID - Name (Type)" or "🕒 ID - Name (Type)"
        if val.startswith("🕒 "):
            val = val[2:]
        eq_id = val.split(" - ")[0]
        
        # Add to history
        facility = self.facility_provider()
        eq = facility.get_equipment(eq_id)
        if eq:
            item = (eq.equipment_id, eq.name, eq.type)
            if item in self._history:
                self._history.remove(item)
            self._history.append(item)
            # Keep only last 5
            if len(self._history) > 5:
                self._history.pop(0)

        self._hide_dropdown()
        self.entry.delete(0, "end")
        eq_name = f"{eq_id}" if not eq else f"{eq.name}"
        self.entry.insert(0, eq_name)
        self.focus_set()

        if self.on_select:
            logger.info(f"Focus executed for eq_id: {eq_id}")
            self.on_select(eq_id)
