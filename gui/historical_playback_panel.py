import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import dateutil.parser

from gui.theme import FONT_TITLE, FONT_LABEL

class HistoricalPlaybackPanel(ttk.Frame):
    def __init__(self, parent: tk.Widget, historian, on_play_cb=None, on_stop_cb=None, on_seek_cb=None):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self.historian = historian
        self.on_play_cb = on_play_cb
        self.on_stop_cb = on_stop_cb
        self.on_seek_cb = on_seek_cb
        
        self._is_playing = False
        
        # Determine times
        min_ts, max_ts = self.historian.get_time_range()
        if not min_ts or not max_ts:
            # Fallback if DB empty
            now = datetime.now()
            self.min_time = now - timedelta(hours=1)
            self.max_time = now
        else:
            self.min_time = dateutil.parser.parse(min_ts)
            self.max_time = dateutil.parser.parse(max_ts)
            
        self.current_time = self.min_time
        self.total_seconds = (self.max_time - self.min_time).total_seconds()
        
        self._build_ui()
        self._update_time_label()
        
    def _build_ui(self):
        # Header
        header = ttk.Frame(self)
        header.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(header, text="HISTORICAL PLAYBACK", font=FONT_TITLE).pack(side=tk.LEFT)
        
        # Main controls container
        controls = ttk.LabelFrame(self, text="Playback Controls", padding=20)
        controls.pack(fill=tk.X, pady=10)
        
        # Timeline Slider
        slider_frame = ttk.Frame(controls)
        slider_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.lbl_current = ttk.Label(slider_frame, text="00:00:00", font=FONT_LABEL)
        self.lbl_current.pack(side=tk.LEFT, padx=10)
        
        self.slider = ttk.Scale(slider_frame, from_=0, to=max(1, self.total_seconds), orient="horizontal", command=self._on_slider_drag)
        self.slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        self.lbl_max = ttk.Label(slider_frame, text=self.max_time.strftime("%Y-%m-%d %H:%M:%S"), font=FONT_LABEL)
        self.lbl_max.pack(side=tk.LEFT, padx=10)
        
        # Buttons
        btn_frame = ttk.Frame(controls)
        btn_frame.pack(fill=tk.X)
        
        self.btn_play = ttk.Button(btn_frame, text="▶ Play", command=self._toggle_play)
        self.btn_play.pack(side=tk.LEFT, padx=5)
        
        self.btn_stop = ttk.Button(btn_frame, text="⏹ Stop (Live)", command=self._stop)
        self.btn_stop.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(btn_frame, text="Playback Speed:").pack(side=tk.LEFT, padx=(20, 5))
        self.var_speed = tk.IntVar(value=1)
        speed_opts = [1, 2, 5, 10, 60]
        self.cb_speed = ttk.Combobox(btn_frame, textvariable=self.var_speed, values=speed_opts, state="readonly", width=5)
        self.cb_speed.pack(side=tk.LEFT)
        self.cb_speed.bind("<<ComboboxSelected>>", self._on_speed_change)
        
        # Jump To
        jump_frame = ttk.Frame(controls)
        jump_frame.pack(fill=tk.X, pady=15)
        ttk.Label(jump_frame, text="Jump to Timestamp (YYYY-MM-DD HH:MM:SS):").pack(side=tk.LEFT, padx=5)
        self.var_jump = tk.StringVar()
        self.ent_jump = ttk.Entry(jump_frame, textvariable=self.var_jump, width=22)
        self.ent_jump.pack(side=tk.LEFT, padx=5)
        ttk.Button(jump_frame, text="Go", command=self._jump_to).pack(side=tk.LEFT, padx=5)
        
    def _update_time_label(self):
        self.lbl_current.config(text=self.current_time.strftime("%Y-%m-%d %H:%M:%S"))
        
    def _on_slider_drag(self, val):
        secs = float(val)
        self.current_time = self.min_time + timedelta(seconds=secs)
        self._update_time_label()
        if not self._is_playing and self.on_seek_cb:
            self.on_seek_cb(self.current_time.isoformat())
            
    def _toggle_play(self):
        if self._is_playing:
            self._is_playing = False
            self.btn_play.config(text="▶ Play")
            if self.on_stop_cb: self.on_stop_cb(pause_only=True)
        else:
            self._is_playing = True
            self.btn_play.config(text="⏸ Pause")
            if self.on_play_cb:
                self.on_play_cb(self.current_time.isoformat(), self.var_speed.get())
                
    def _stop(self):
        self._is_playing = False
        self.btn_play.config(text="▶ Play")
        # Jump slider to end visually
        self.slider.set(self.total_seconds)
        self.current_time = self.max_time
        self._update_time_label()
        if self.on_stop_cb:
            self.on_stop_cb(pause_only=False)
            
    def _on_speed_change(self, event):
        if self._is_playing and self.on_play_cb:
            self.on_play_cb(self.current_time.isoformat(), self.var_speed.get())
            
    def _jump_to(self):
        try:
            target = dateutil.parser.parse(self.var_jump.get())
            if target < self.min_time: target = self.min_time
            if target > self.max_time: target = self.max_time
            
            self.current_time = target
            offset_secs = (self.current_time - self.min_time).total_seconds()
            self.slider.set(offset_secs)
            self._update_time_label()
            
            if self.on_seek_cb:
                self.on_seek_cb(self.current_time.isoformat())
                
        except Exception:
            import tkinter.messagebox as mb
            mb.showerror("Invalid Date", "Please enter a valid datetime string.")

    def update_playback_time(self, current_iso: str):
        """Called externally by main loop to advance the slider automatically while playing."""
        try:
            self.current_time = dateutil.parser.parse(current_iso)
            offset_secs = (self.current_time - self.min_time).total_seconds()
            
            # Briefly disable slider command to avoid infinite loop
            self.slider.config(command="")
            self.slider.set(offset_secs)
            self.slider.config(command=self._on_slider_drag)
            
            self._update_time_label()
            
            if self.current_time >= self.max_time:
                self._stop()
        except:
            pass
