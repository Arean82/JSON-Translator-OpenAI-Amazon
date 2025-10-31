# utils/language_manager.py
import tkinter as tk
from tkinter import messagebox
import json
import os
from typing import List, Dict

# File paths
LANG_FILE = os.path.join("data", "languages.json")
LANG_MAP_FILE = os.path.join("data", "lang_map.json")
DEFAULT_LANGS = ["ar", "fr", "es"]

# Load language map
def load_language_map() -> Dict[str, str]:
    """Load ISO code to language name mapping"""
    if os.path.exists(LANG_MAP_FILE):
        with open(LANG_MAP_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {"ar": "Arabic", "fr": "French", "es": "Spanish"}  # fallback

ISO_LANG_MAP = load_language_map()

# Load user-selected languages
def load_user_languages() -> List[str]:
    """Load user's selected languages"""
    if os.path.exists(LANG_FILE):
        try:
            with open(LANG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_LANGS.copy()
    else:
        return DEFAULT_LANGS.copy()

def save_user_languages(languages: List[str]):
    """Save user's selected languages"""
    with open(LANG_FILE, "w", encoding="utf-8") as f:
        json.dump(languages, f, ensure_ascii=False, indent=2)

def get_languages() -> List[str]:
    """Get user's selected languages"""
    return load_user_languages()

def get_language_name(lang_code: str) -> str:
    """Get language name from ISO code"""
    return ISO_LANG_MAP.get(lang_code, lang_code)

def open_language_popup(root):
    """Popup for managing languages"""
    popup = tk.Toplevel(root)
    popup.title("Manage Languages")
    popup.geometry("400x320")
    popup.resizable(False, False)

    tk.Label(popup, text="Add Language (ISO code):").pack(pady=(10,0))
    new_lang_var = tk.StringVar()
    tk.Entry(popup, textvariable=new_lang_var).pack(pady=(0,10))

    listbox = tk.Listbox(popup)
    listbox.pack(fill="both", expand=True, padx=10, pady=10)

    def refresh_listbox():
        listbox.delete(0, tk.END)
        for code in get_languages():
            name = get_language_name(code)
            listbox.insert(tk.END, f"{code} - {name}")

    refresh_listbox()

    def add_language():
        code = new_lang_var.get().strip().lower()
        if not code:
            messagebox.showwarning("Invalid", "Language code cannot be empty")
            return
        if code not in ISO_LANG_MAP:
            messagebox.showwarning("Invalid", f"{code} not found in language map")
            return
        
        current_langs = get_languages()
        if code in current_langs:
            messagebox.showwarning("Duplicate", f"{code} already in the list")
            return
        
        current_langs.append(code)
        save_user_languages(current_langs)
        new_lang_var.set("")
        refresh_listbox()

    def remove_selected():
        sel = listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        current_langs = get_languages()
        if idx < len(current_langs):
            removed_code = current_langs[idx]
            current_langs.remove(removed_code)
            save_user_languages(current_langs)
            refresh_listbox()

    tk.Button(popup, text="Add", command=add_language).pack(side="left", padx=10, pady=5)
    tk.Button(popup, text="Remove Selected", command=remove_selected).pack(side="right", padx=10, pady=5)

    popup.transient(root)
    popup.grab_set()
    root.wait_window(popup)

    