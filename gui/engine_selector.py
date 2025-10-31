# gui/engine_selector.py
import os
import json
import subprocess
import sys
from tkinter import *
from tkinter import messagebox, simpledialog
from pathlib import Path

from utils.credentials_manager import save_credentials, load_credentials

class EngineSelector:
    def __init__(self, root):
        self.root = root
        self.setup_window()
        self.create_widgets()
        
    def setup_window(self):
        self.root.title("JSON Translator – Engine Setup")
        self.root.geometry("400x280")
        self.root.resizable(False, False)
        
    def create_widgets(self):
        # Header
        Label(self.root, text="Select Translation Engine", font=("Arial", 14, "bold")).pack(pady=15)
        
        # Engine selection
        self.engine_var = StringVar(value="openai")
        
        engine_frame = Frame(self.root)
        engine_frame.pack(pady=10)
        
        Radiobutton(engine_frame, text="OpenAI", variable=self.engine_var, 
                   value="openai", font=("Arial", 11)).grid(row=0, column=0, sticky=W, padx=20)
        Radiobutton(engine_frame, text="Amazon Translate", variable=self.engine_var, 
                   value="amazon", font=("Arial", 11)).grid(row=1, column=0, sticky=W, padx=20)
        Radiobutton(engine_frame, text="DeepSeek (Local)", variable=self.engine_var, 
                   value="deepseek", font=("Arial", 11)).grid(row=2, column=0, sticky=W, padx=20)
        
        # Buttons
        button_frame = Frame(self.root)
        button_frame.pack(pady=20)
        
        Button(
            button_frame,
            text="Check / Add API Keys",
            command=self.verify_engine_credentials,
            bg="#1976d2",
            fg="white",
            font=("Arial", 10),
            width=15
        ).pack(side=LEFT, padx=5)
        
        Button(
            button_frame,
            text="Continue →",
            bg="#2e7d32",
            fg="white",
            font=("Arial", 11, "bold"),
            width=15,
            command=self.launch_main_gui
        ).pack(side=LEFT, padx=5)
        
        # Footer
        Label(self.root, text="© 2025 JSON Translator", fg="gray", 
              font=("Arial", 8)).pack(side=BOTTOM, pady=10)
    
    def verify_engine_credentials(self):
        engine = self.engine_var.get()
        creds = load_credentials()
        
        if engine == "deepseek":
            messagebox.showinfo("DeepSeek Local", 
                              "DeepSeek runs locally - no API keys needed!\n"
                              "You'll download models when you first use it.")
            return

        if engine not in creds:
            res = messagebox.askyesno(
                "Credentials Missing",
                f"No credentials found for {engine.capitalize()}.\nDo you want to add them now?"
            )
            if res:
                self.prompt_for_credentials(engine)
        else:
            messagebox.showinfo("Credentials Found", 
                              f"{engine.capitalize()} credentials are available.")
    
    def prompt_for_credentials(self, engine):
        if engine == "openai":
            key = simpledialog.askstring("OpenAI API Key", "Enter your OpenAI API Key (sk-...):", show="*")
            if not key:
                messagebox.showerror("Error", "API key cannot be empty.")
                return
            save_credentials("openai", {"openai_key": key})

        elif engine == "amazon":
            access = simpledialog.askstring("AWS Access Key", "Enter your AWS Access Key:")
            secret = simpledialog.askstring("AWS Secret Key", "Enter your AWS Secret Key:", show="*")
            if not access or not secret:
                messagebox.showerror("Error", "Both AWS keys are required.")
                return
            save_credentials("amazon", {"aws_access_key": access, "aws_secret_key": secret})
    
    def launch_main_gui(self):
        """Launch the main translation GUI"""
        engine = self.engine_var.get()
        
        try:
            # Import and launch main window
            from gui.main_window import MainWindow
            from core.translation_engine import TranslationEngine
            
            # Create translation engine
            translation_engine = TranslationEngine()
            
            # Create new window for main GUI
            main_root = Toplevel(self.root)
            main_root.withdraw()  # Hide initially
            
            app = MainWindow(main_root, translation_engine, engine)
            
            # Center and show
            main_root.deiconify()
            self.root.withdraw()  # Hide selector
            
            # Handle window close
            def on_closing():
                self.root.destroy()
            
            main_root.protocol("WM_DELETE_WINDOW", on_closing)
            
        except Exception as e:
            messagebox.showerror("Launch Error", f"Failed to open main GUI:\n{e}")

def main():
    root = Tk()
    app = EngineSelector(root)
    root.mainloop()

if __name__ == "__main__":
    main()

    