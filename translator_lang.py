# translator_lang.py

import tkinter as tk
from tkinter import messagebox
import json, os

# -----------------------------
# File paths and defaults
# -----------------------------
LANG_FILE = "languages.json"       # user-selected languages
LANG_MAP_FILE = "lang_map.json"    # ISO → Language Name
DEFAULT_LANGS = ["ar", "fr", "es"]

# -----------------------------
# Load language map
# -----------------------------
if os.path.exists(LANG_MAP_FILE):
    with open(LANG_MAP_FILE, "r", encoding="utf-8") as f:
        ISO_LANG_MAP = json.load(f)
else:
    ISO_LANG_MAP = {"ar": "Arabic", "fr": "French", "es": "Spanish"}  # fallback

# -----------------------------
# Load user-selected languages
# -----------------------------
if os.path.exists(LANG_FILE):
    try:
        with open(LANG_FILE, "r", encoding="utf-8") as f:
            languages = json.load(f)
    except Exception:
        languages = DEFAULT_LANGS.copy()
else:
    languages = DEFAULT_LANGS.copy()

# -----------------------------
# Save/load helpers
# -----------------------------
def save_languages():
    with open(LANG_FILE, "w", encoding="utf-8") as f:
        json.dump(languages, f, ensure_ascii=False, indent=2)

def get_languages():
    return languages.copy()

# -----------------------------
# Popup for managing languages
# -----------------------------
def open_language_popup(root):
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
        for code in languages:
            name = ISO_LANG_MAP.get(code, "Unknown")
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
        if code in languages:
            messagebox.showwarning("Duplicate", f"{code} already in the list")
            return
        languages.append(code)
        new_lang_var.set("")
        save_languages()
        refresh_listbox()

    def remove_selected():
        sel = listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        code = languages[idx]
        languages.remove(code)
        save_languages()
        refresh_listbox()

    tk.Button(popup, text="Add", command=add_language).pack(side="left", padx=10, pady=5)
    tk.Button(popup, text="Remove Selected", command=remove_selected).pack(side="right", padx=10, pady=5)

    popup.transient(root)
    popup.grab_set()
    root.wait_window(popup)
