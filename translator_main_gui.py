import os
import json
import argparse
from tkinter import *
from tkinter import ttk, messagebox
from translator_gui_functions import browse_file, start_or_cancel_translation, show_messages_popup
from translator_lang import get_languages, open_language_popup

# --------------------------
# Parse engine from arguments
# --------------------------
parser = argparse.ArgumentParser(description="JSON Translator Main GUI")
parser.add_argument("--engine", required=True, help="Translation engine: openai or amazon")
args = parser.parse_args()
ENGINE = args.engine.lower().strip()

CREDENTIALS_FILE = "api_credentials.json"

# Load credentials
if not os.path.exists(CREDENTIALS_FILE):
    messagebox.showerror("Missing Credentials", f"Credentials file not found:\n{CREDENTIALS_FILE}")
    raise SystemExit

with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
    creds_all = json.load(f)

if ENGINE not in creds_all:
    messagebox.showerror("Missing Engine Keys", f"No credentials found for '{ENGINE}' in {CREDENTIALS_FILE}")
    raise SystemExit

CREDENTIALS = creds_all[ENGINE]

# --------------------------
# Root Window Setup
# --------------------------
root = Tk()
root.title(f"JSON Translator – {ENGINE.capitalize()}")
root.geometry("440x460")  # Slightly taller for macOS visibility
root.resizable(False, False)

status_text = []
status_message = StringVar(value="")  # For success/fail message

# --------------------------
# Menu Bar
# --------------------------
menu_bar = Menu(root)
root.config(menu=menu_bar)

messages_menu = Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Messages", menu=messages_menu)
messages_menu.add_command(label="View Messages", command=lambda: show_messages_popup(root, status_text))

file_menu = Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Exit", command=root.quit)

# --------------------------
# Header
# --------------------------
header_frame = Frame(root)
header_frame.pack(fill=X, padx=10, pady=10)
Label(header_frame, text="JSON Translator", font=("Arial", 15, "bold")).pack()
Label(header_frame, text=f"Engine: {ENGINE.capitalize()}", fg="gray").pack()

# --------------------------
# Content Area
# --------------------------
content_frame = Frame(root)
content_frame.pack(fill=BOTH, expand=True, padx=15, pady=(0, 10))

file_path = StringVar()
engine_var = StringVar(value=ENGINE)

# File selection
Label(content_frame, text="Select Source JSON File:").pack(anchor=W)
file_frame = Frame(content_frame)
file_frame.pack(fill=X, pady=(0, 5))
Entry(file_frame, textvariable=file_path, width=40).pack(side=LEFT, fill=X, expand=True)
Button(file_frame, text="Browse", command=lambda: browse_file(file_path)).pack(side=LEFT, padx=5)

# Source language
Label(content_frame, text="Source Language:").pack(anchor=W, pady=(5, 0))
source_lang_entry = Entry(content_frame, width=30)
source_lang_entry.insert(0, "en")
source_lang_entry.pack(fill=X, pady=(0, 5))

# Target languages
langs_frame = Frame(content_frame)
langs_frame.pack(fill=X, pady=(5, 5))
Label(langs_frame, text="Target Languages:").pack(side=LEFT, anchor=W)
current_langs_var = StringVar(value=", ".join(get_languages()))
Label(langs_frame, textvariable=current_langs_var, fg="blue").pack(side=LEFT, padx=(5, 10))
Button(
    langs_frame,
    text="Manage Languages",
    command=lambda: [
        open_language_popup(root),
        current_langs_var.set(", ".join(get_languages()))
    ],
).pack(side=LEFT)

# Mode selection
mode_var = StringVar(value="nonblog")
mode_frame = Frame(content_frame)
mode_frame.pack(fill=X, pady=(10, 10))
Label(mode_frame, text="Mode:").pack(side=LEFT, padx=(0, 5))
mode_toggle = ttk.Checkbutton(
    mode_frame,
    text="Blog Mode",
    variable=mode_var,
    onvalue="blog",
    offvalue="nonblog",
)
mode_toggle.pack(side=LEFT)

# Progress bar
progress_bar = ttk.Progressbar(content_frame, orient="horizontal", length=380, mode="determinate")
progress_bar.pack(pady=(5, 10))

# --------------------------
# Start Button + Status
# --------------------------
def handle_translation():
    """Start translation without showing premature success messages."""
    # Clear old message
    status_message.set("")
    try:
        start_or_cancel_translation(
            root,
            start_btn,
            file_path,
            source_lang_entry,
            current_langs_var,
            engine_var,
            status_label,
            status_text,
            progress_bar,
            mode_var,
        )
    except Exception as e:
        status_message.set(f"❌ Translation failed: {e}")


start_btn = Button(
    content_frame,
    text="Start Translation",
    bg="#2e7d32",
    fg="white",
    font=("Arial", 12, "bold"),
    height=2,
    command=handle_translation,
)
start_btn.pack(pady=(5, 10), fill=X)

# Final message label (below button)
status_label = Label(root, textvariable=status_message, font=("Arial", 11), fg="blue")
status_label.pack(pady=(0, 10))

# --------------------------
# Footer
# --------------------------
footer = Frame(root)
footer.pack(fill=X, side=BOTTOM, pady=5)
Label(
    footer,
    text="© 2025 JSON Translator – Human-like Output",
    fg="gray",
    font=("Arial", 8),
).pack(fill=X)

root.mainloop()
