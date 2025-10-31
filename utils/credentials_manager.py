# utils/credentials_manager.py
import os
import sys
import json
from tkinter import messagebox

API_KEY_FILENAME = "api_credentials.json"

def get_app_base_path():
    """Return the directory of the running script or executable."""
    if getattr(sys, 'frozen', False):
        # Running as compiled exe (PyInstaller)
        return os.path.dirname(sys.executable)
    else:
        # Running as normal Python script
        return os.path.dirname(os.path.abspath(__file__))

def get_credentials_path():
    """Return the absolute path to api_credentials.json inside app directory."""
    base_path = get_app_base_path()
    return os.path.join(base_path, "..", "data", API_KEY_FILENAME)

def save_credentials(engine, creds):
    """
    Save credentials in the application directory.
    """
    key_file_path = get_credentials_path()
    # Load existing data
    try:
        with open(key_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        data = {}
    
    # Update with new credentials
    data[engine] = creds
    
    try:
        with open(key_file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Credentials saved in {key_file_path}")
    except Exception as e:
        messagebox.showwarning("Warning", f"Could not save credentials:\n{e}")

def load_credentials():
    """
    Load credentials from application directory.
    Returns dict of all credentials
    """
    key_file_path = get_credentials_path()
    if os.path.exists(key_file_path):
        try:
            with open(key_file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            messagebox.showwarning("Warning", f"Could not read saved credentials:\n{e}")
    return {}

def clear_credentials(engine=None):
    """
    Delete credentials from the application directory.
    If engine is None, clear all credentials.
    """
    key_file_path = get_credentials_path()
    if os.path.exists(key_file_path):
        try:
            if engine:
                # Remove specific engine credentials
                with open(key_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if engine in data:
                    del data[engine]
                    with open(key_file_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                # Remove all credentials
                os.remove(key_file_path)
            print(f"🧹 Credentials cleared from {key_file_path}")
        except Exception as e:
            messagebox.showwarning("Warning", f"Could not delete credentials:\n{e}")

            