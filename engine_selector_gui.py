import os
import json
import subprocess
import sys
from tkinter import *
from tkinter import messagebox, simpledialog
from pathlib import Path

# --------------------------------
# CONFIG
# --------------------------------
APP_DIR = Path(__file__).parent
CREDENTIALS_FILE = APP_DIR / "api_credentials.json"
MAIN_GUI = APP_DIR / "translator_main_gui.py"

# --------------------------------
# Credentials management
# --------------------------------
def load_credentials():
    if CREDENTIALS_FILE.exists():
        try:
            with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Invalid credentials file format.")
    return {}

def save_credentials(data):
    with open(CREDENTIALS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    messagebox.showinfo("Saved", f"✅ Credentials saved to {CREDENTIALS_FILE}")

def prompt_for_credentials(engine):
    creds = load_credentials()

    if engine == "openai":
        key = simpledialog.askstring("OpenAI API Key", "Enter your OpenAI API Key (sk-...):", show="*")
        if not key:
            messagebox.showerror("Error", "API key cannot be empty.")
            return False
        creds["openai"] = {"openai_key": key}

    elif engine == "amazon":
        access = simpledialog.askstring("AWS Access Key", "Enter your AWS Access Key:")
        secret = simpledialog.askstring("AWS Secret Key", "Enter your AWS Secret Key:", show="*")
        if not access or not secret:
            messagebox.showerror("Error", "Both AWS keys are required.")
            return False
        creds["amazon"] = {"aws_access_key": access, "aws_secret_key": secret}

    save_credentials(creds)
    return True

def verify_engine_credentials():
    engine = engine_var.get()
    creds = load_credentials()

    if engine not in creds:
        res = messagebox.askyesno(
            "Credentials Missing",
            f"No credentials found for {engine.capitalize()}.\nDo you want to add them now?"
        )
        if res:
            prompt_for_credentials(engine)
    else:
        messagebox.showinfo("Credentials Found", f"{engine.capitalize()} credentials are available.")

def launch_main_gui(engine):
    """Launch translator_main_gui.py with the selected engine."""
    if not MAIN_GUI.exists():
        messagebox.showerror("Error", f"Cannot find translator_main_gui.py in:\n{MAIN_GUI}")
        return

    creds = load_credentials()
    if engine not in creds:
        messagebox.showerror("Error", f"No credentials found for {engine.capitalize()}.\nPlease add them first.")
        return

    try:
        subprocess.Popen([sys.executable, str(MAIN_GUI), "--engine", engine], cwd=APP_DIR)
        root.destroy()  # Close the selector window
    except Exception as e:
        messagebox.showerror("Launch Error", f"Failed to open main GUI:\n{e}")

# --------------------------------
# UI
# --------------------------------
root = Tk()
root.title("JSON Translator – Engine Setup")
root.geometry("360x230")
root.resizable(False, False)

Label(root, text="Select Translation Engine", font=("Arial", 14, "bold")).pack(pady=10)

engine_var = StringVar(value="openai")
Radiobutton(root, text="OpenAI", variable=engine_var, value="openai").pack(anchor=W, padx=30)
Radiobutton(root, text="Amazon Translate", variable=engine_var, value="amazon").pack(anchor=W, padx=30)

Button(
    root,
    text="Check / Add API Keys",
    command=verify_engine_credentials,
    bg="#1976d2",
    fg="white"
).pack(pady=12, fill=X, padx=40)

Button(
    root,
    text="Continue →",
    bg="#2e7d32",
    fg="white",
    font=("Arial", 11, "bold"),
    command=lambda: launch_main_gui(engine_var.get())
).pack(pady=5, fill=X, padx=40)

Label(root, text="© 2025 JSON Translator", fg="gray", font=("Arial", 8)).pack(side=BOTTOM, pady=5)

root.mainloop()
