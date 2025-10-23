#  credentials_manager.py

import os
import json
from tkinter import messagebox

API_KEY_FILENAME = "api_credentials.json"

def save_credentials(engine, creds, folder):
    """
    Save credentials for the selected engine in the folder.
    """
    if not folder:
        folder = os.getcwd()
    key_file_path = os.path.join(folder, API_KEY_FILENAME)
    data = {
        "engine": engine,
        "creds": creds
    }
    try:
        with open(key_file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Credentials saved in {key_file_path}")
    except Exception as e:
        messagebox.showwarning("Warning", f"Could not save credentials:\n{e}")

def load_credentials(folder):
    """
    Load saved credentials if they exist.
    Returns (engine, creds) or (None, None)
    """
    if not folder:
        folder = os.getcwd()
    key_file_path = os.path.join(folder, API_KEY_FILENAME)
    if os.path.exists(key_file_path):
        try:
            with open(key_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                engine = data.get("engine")
                creds = data.get("creds")
                if engine and creds:
                    return engine, creds
        except Exception as e:
            messagebox.showwarning("Warning", f"Could not read saved credentials:\n{e}")
    return None, None

def clear_credentials(folder):
    """
    Delete saved credentials if needed.
    """
    if not folder:
        folder = os.getcwd()
    key_file_path = os.path.join(folder, API_KEY_FILENAME)
    if os.path.exists(key_file_path):
        try:
            os.remove(key_file_path)
            print(f"Credentials cleared from {key_file_path}")
        except Exception as e:
            messagebox.showwarning("Warning", f"Could not delete credentials:\n{e}")
