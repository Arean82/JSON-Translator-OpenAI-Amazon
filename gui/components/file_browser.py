# gui/components/file_browser.py
import tkinter as tk
from tkinter import ttk, filedialog
from typing import Optional, Callable

class FileBrowser(ttk.Frame):
    def __init__(self, parent, label_text: str = "Select File:", 
                 file_types: list = None, on_file_select: Optional[Callable] = None):
        super().__init__(parent)
        self.file_types = file_types or [("All files", "*.*")]
        self.on_file_select = on_file_select
        self.create_widgets(label_text)
        
    def create_widgets(self, label_text: str):
        # Label
        ttk.Label(self, text=label_text).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # File path entry and browse button
        self.file_var = tk.StringVar()
        
        entry_frame = ttk.Frame(self)
        entry_frame.grid(row=1, column=0, columnspan=2, sticky=tk.EW)
        entry_frame.columnconfigure(0, weight=1)
        
        self.file_entry = ttk.Entry(entry_frame, textvariable=self.file_var)
        self.file_entry.grid(row=0, column=0, sticky=tk.EW, padx=(0, 5))
        
        ttk.Button(
            entry_frame,
            text="Browse",
            command=self.browse_file
        ).grid(row=0, column=1)
        
        self.columnconfigure(0, weight=1)
        
    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=self.file_types)
        if filename:
            self.file_var.set(filename)
            if self.on_file_select:
                self.on_file_select(filename)
                
    def get_file_path(self) -> str:
        return self.file_var.get()
    
    def set_file_path(self, path: str):
        self.file_var.set(path)
        
    def clear(self):
        self.file_var.set("")

        