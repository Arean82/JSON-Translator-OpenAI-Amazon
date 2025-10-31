# gui/components/status_display.py
import tkinter as tk
from tkinter import ttk
from typing import Optional

class StatusDisplay(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()
        
    def create_widgets(self):
        # Status text
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(
            self, 
            textvariable=self.status_var,
            wraplength=400,
            justify=tk.LEFT
        )
        self.status_label.pack(fill=tk.X)
        
    def set_status(self, message: str, status_type: str = "info"):
        """Set status message with type-based styling"""
        self.status_var.set(message)
        
        # Set color based on status type
        colors = {
            "info": "black",
            "success": "green",
            "warning": "orange",
            "error": "red",
            "progress": "blue"
        }
        
        color = colors.get(status_type, "black")
        self.status_label.config(foreground=color)
        
    def clear_status(self):
        """Clear status message"""
        self.status_var.set("Ready")
        self.status_label.config(foreground="black")
        
    def set_success(self, message: str):
        """Set success status"""
        self.set_status(message, "success")
        
    def set_error(self, message: str):
        """Set error status"""
        self.set_status(message, "error")
        
    def set_warning(self, message: str):
        """Set warning status"""
        self.set_status(message, "warning")
        
    def set_progress(self, message: str):
        """Set progress status"""
        self.set_status(message, "progress")

        