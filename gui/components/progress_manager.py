# gui/components/progress_manager.py
import tkinter as tk
from tkinter import ttk
from typing import Optional

class ProgressManager(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.total_items = 0
        self.current_progress = 0
        self.create_widgets()
        
    def create_widgets(self):
        # Progress bar
        self.progress_bar = ttk.Progressbar(self, orient="horizontal", mode="determinate")
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))
        
        # Progress label
        self.progress_label = ttk.Label(self, text="Ready", foreground="gray")
        self.progress_label.pack(fill=tk.X)
        
    def start_progress(self, total_items: int = 100):
        """Start progress tracking"""
        self.total_items = total_items
        self.current_progress = 0
        self.progress_bar["value"] = 0
        self.progress_bar["maximum"] = total_items
        self.progress_label.config(text="Starting...")
        
    def update_progress(self, increment: int = 1):
        """Update progress by increment"""
        self.current_progress += increment
        self.progress_bar["value"] = self.current_progress
        
        if self.total_items > 0:
            percentage = (self.current_progress / self.total_items) * 100
            self.progress_label.config(
                text=f"Progress: {self.current_progress}/{self.total_items} ({percentage:.1f}%)"
            )
        else:
            self.progress_label.config(text=f"Progress: {self.current_progress} items")
            
    def set_progress(self, value: int, maximum: Optional[int] = None):
        """Set progress to specific value"""
        if maximum is not None:
            self.progress_bar["maximum"] = maximum
            self.total_items = maximum
            
        self.progress_bar["value"] = value
        self.current_progress = value
        
        if maximum and maximum > 0:
            percentage = (value / maximum) * 100
            self.progress_label.config(text=f"Progress: {value}/{maximum} ({percentage:.1f}%)")
        else:
            self.progress_label.config(text=f"Progress: {value}")
            
    def complete_progress(self):
        """Mark progress as complete"""
        self.progress_bar["value"] = self.progress_bar["maximum"]
        self.progress_label.config(text="Completed!", foreground="green")
        
    def reset_progress(self):
        """Reset progress to initial state"""
        self.total_items = 0
        self.current_progress = 0
        self.progress_bar["value"] = 0
        self.progress_label.config(text="Ready", foreground="gray")
        
    def set_indeterminate(self):
        """Switch to indeterminate mode"""
        self.progress_bar.config(mode="indeterminate")
        self.progress_bar.start()
        self.progress_label.config(text="Processing...")
        
    def set_determinate(self):
        """Switch to determinate mode"""
        self.progress_bar.config(mode="determinate")
        self.progress_bar.stop()
        self.progress_label.config(text="Ready")

        