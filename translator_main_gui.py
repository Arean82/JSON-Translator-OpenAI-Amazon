# JSON Translator Main GUI

from tkinter import *
from tkinter import ttk
from translator_gui_functions import browse_file, start_or_cancel_translation, show_messages_popup
from translator_lang import get_languages, open_language_popup

root = Tk()
root.title("JSON Translator – OpenAI/Amazon")
root.geometry("420x420")
root.resizable(False, False)

status_text = []

# ----------------------
# Menu
# ----------------------
menu_bar = Menu(root)
root.config(menu=menu_bar)

messages_menu = Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Messages", menu=messages_menu)
messages_menu.add_command(label="View Messages", command=lambda: show_messages_popup(root, status_text))

file_menu = Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Exit", command=root.quit)

# ----------------------
# Header
# ----------------------
header_frame = Frame(root)
header_frame.pack(fill=X, padx=10, pady=5)
Label(header_frame, text="JSON Translator", font=("Arial", 14, "bold")).pack()
Label(header_frame, text="Translate JSON naturally using OpenAI or Amazon.", fg="gray").pack()

# ----------------------
# Content
# ----------------------
content_frame = Frame(root)
content_frame.pack(fill=BOTH, expand=True, padx=10)

file_path = StringVar()
engine_var = StringVar(value="openai")

# File selection
Label(content_frame, text="Select Source JSON File:").pack(anchor=W)
file_frame = Frame(content_frame)
file_frame.pack(fill=X)
Entry(file_frame, textvariable=file_path, width=40).pack(side=LEFT, fill=X, expand=True)
Button(file_frame, text="Browse", command=lambda: browse_file(file_path)).pack(side=LEFT, padx=5)

# Source language
Label(content_frame, text="Source Language:").pack(anchor=W, pady=(5,0))
source_lang_entry = Entry(content_frame, width=30)
source_lang_entry.insert(0, "en")
source_lang_entry.pack(fill=X)

# ----------------------
# Languages management
# ----------------------
langs_frame = Frame(content_frame)
langs_frame.pack(fill=X, pady=(5,5))

# Label for description
Label(langs_frame, text="Target Languages:").pack(side=LEFT, anchor=W)

# Label to show current languages
current_langs_var = StringVar()
current_langs_var.set(", ".join(get_languages()))
Label(langs_frame, textvariable=current_langs_var, fg="blue").pack(side=LEFT, padx=(5,10))

# Manage Languages button
Button(langs_frame, text="Manage Languages",
       command=lambda: [open_language_popup(root), current_langs_var.set(", ".join(get_languages()))]
       ).pack(side=LEFT)

# Engine selection
Label(content_frame, text="Translation Engine:").pack(anchor=W, pady=(5,0))
engine_dropdown = ttk.Combobox(content_frame, textvariable=engine_var, values=["openai", "amazon"], state="readonly")
engine_dropdown.pack(fill=X)

# Progress bar
progress_bar = ttk.Progressbar(content_frame, orient="horizontal", length=400, mode="determinate")
progress_bar.pack(pady=5)

# Status label
status_label = Label(content_frame, text="", fg="blue", wraplength=400, justify=CENTER)
status_label.pack()

# Start/Cancel button
start_btn = Button(content_frame, text="Start Translation", bg="#2e7d32", fg="white", font=("Arial", 12, "bold"),
                   command=lambda: start_or_cancel_translation(root, start_btn, file_path, source_lang_entry,
                                                               current_langs_var, engine_var, status_label,
                                                               status_text, progress_bar))
start_btn.pack(pady=10)

# ----------------------
# Footer
# ----------------------
footer_frame = Frame(root)
footer_frame.pack(fill=X, side=BOTTOM)
Label(footer_frame, text="© 2025 JSON Translator – Human-like Output", fg="gray", font=("Arial", 8)).pack(fill=X)

root.mainloop()
