# gui/deepseek_window.py
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import Optional

from engines.deepseek_engine import (
    get_deepseek_model_status, 
    load_deepseek_model, 
    unload_deepseek_model,
    download_deepseek_model,
    get_deepseek_client
)

class DeepSeekWindow:
    def __init__(self, root):
        self.root = root
        self.llm, self.manager = get_deepseek_client()
        self.setup_window()
        self.create_widgets()
        self.update_status()
        
    def setup_window(self):
        self.root.title("DeepSeek Model Management")
        self.root.geometry("500x400")
        self.root.minsize(450, 350)
        
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        ttk.Label(
            main_frame, 
            text="DeepSeek Model Management", 
            font=("Arial", 14, "bold")
        ).pack(pady=(0, 20))
        
        # Model selection
        self.create_model_section(main_frame)
        
        # Status display
        self.create_status_section(main_frame)
        
        # Action buttons
        self.create_action_section(main_frame)
        
        # Memory info
        self.create_memory_section(main_frame)
        
    def create_model_section(self, parent):
        model_frame = ttk.LabelFrame(parent, text="Model Selection", padding="10")
        model_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(model_frame, text="Select Model:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(model_frame, textvariable=self.model_var, state="readonly")
        self.model_combo.grid(row=0, column=1, sticky=tk.EW, padx=(5, 0), pady=(0, 5))
        
        model_frame.columnconfigure(1, weight=1)
        
        # Update model list
        self.update_model_list()
        
    def create_status_section(self, parent):
        status_frame = ttk.LabelFrame(parent, text="Model Status", padding="10")
        status_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.status_text = tk.Text(
            status_frame, 
            height=6, 
            wrap=tk.WORD,
            font=("Arial", 9)
        )
        self.status_text.pack(fill=tk.BOTH, expand=True)
        self.status_text.config(state=tk.DISABLED)
        
    def create_action_section(self, parent):
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.load_btn = ttk.Button(
            action_frame,
            text="Load Model",
            command=self.load_model
        )
        self.load_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.unload_btn = ttk.Button(
            action_frame,
            text="Unload Model",
            command=self.unload_model
        )
        self.unload_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.download_btn = ttk.Button(
            action_frame,
            text="Download Model",
            command=self.download_model
        )
        self.download_btn.pack(side=tk.LEFT)
        
    def create_memory_section(self, parent):
        memory_frame = ttk.LabelFrame(parent, text="Memory Usage", padding="10")
        memory_frame.pack(fill=tk.X)
        
        self.memory_var = tk.StringVar(value="Memory information will appear here")
        ttk.Label(
            memory_frame,
            textvariable=self.memory_var,
            font=("Arial", 9),
            wraplength=400
        ).pack(fill=tk.X)
        
    def update_model_list(self):
        """Update available models in combobox"""
        available_models = self.manager.get_available_models()
        self.model_combo['values'] = available_models
        
        if available_models:
            self.model_var.set(available_models[0])
            
    def update_status(self):
        """Update model status display"""
        status = get_deepseek_model_status()
        
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete(1.0, tk.END)
        
        if status["model_loaded"]:
            self.status_text.insert(tk.END, f"✅ Model Loaded: {status['current_model']}\n\n")
            self.status_text.insert(tk.END, f"💾 Memory Usage:\n")
            
            memory = status["memory_usage"]
            if memory["device"] == "cuda":
                self.status_text.insert(tk.END, f"  • GPU Allocated: {memory['cuda_allocated']:.2f} GB\n")
                self.status_text.insert(tk.END, f"  • GPU Reserved: {memory['cuda_reserved']:.2f} GB\n")
            else:
                self.status_text.insert(tk.END, f"  • Running on: CPU\n")
                
            # Update memory display
            if memory["device"] == "cuda":
                self.memory_var.set(f"GPU: {memory['cuda_allocated']:.2f} GB allocated, {memory['cuda_reserved']:.2f} GB reserved")
            else:
                self.memory_var.set("Running on CPU")
                
        else:
            self.status_text.insert(tk.END, "❌ No model loaded\n\n")
            self.status_text.insert(tk.END, "Please load a model to start translating.")
            self.memory_var.set("No model loaded")
            
        self.status_text.config(state=tk.DISABLED)
        
        # Update button states
        model_loaded = status["model_loaded"]
        self.load_btn.config(state=tk.NORMAL if not model_loaded else tk.DISABLED)
        self.unload_btn.config(state=tk.NORMAL if model_loaded else tk.DISABLED)
        
    def load_model(self):
        """Load selected model"""
        model_name = self.model_var.get().split(" ")[0]  # Remove status text
        
        def load_thread():
            success, message = load_deepseek_model(model_name)
            self.root.after(0, lambda: self.load_complete(success, message))
            
        threading.Thread(target=load_thread, daemon=True).start()
        messagebox.showinfo("Loading", f"Loading model {model_name}... This may take a moment.")
        
    def load_complete(self, success, message):
        if success:
            messagebox.showinfo("Success", message)
        else:
            messagebox.showerror("Error", message)
        self.update_status()
        
    def unload_model(self):
        """Unload current model"""
        success, message = unload_deepseek_model()
        if success:
            messagebox.showinfo("Success", message)
        else:
            messagebox.showerror("Error", message)
        self.update_status()
        
    def download_model(self):
        """Download selected model"""
        model_name = self.model_var.get().split(" ")[0]
        
        def download_thread():
            success, message = download_deepseek_model(model_name)
            self.root.after(0, lambda: self.download_complete(success, message))
            
        threading.Thread(target=download_thread, daemon=True).start()
        messagebox.showinfo("Download", f"Downloading {model_name}... This may take a while.")
        
    def download_complete(self, success, message):
        if success:
            messagebox.showinfo("Success", message)
            self.update_model_list()
        else:
            messagebox.showerror("Error", message)

            