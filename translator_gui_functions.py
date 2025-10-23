import os
import threading
from tkinter import *
from tkinter import messagebox, filedialog, simpledialog, ttk
from translator_logic import translate, verify_and_prepare_client, load_json, collect_translatable_texts, save_json
from credentials_manager import save_credentials, load_credentials

cancel_flag_global = False  # global flag for canceling translation

# --------------------------
# Status Updates & Popup
# --------------------------
def update_status_label(root, status_label, msg, status_text):
    status_label.config(text=msg)
    status_label.update()
    status_text.append(msg)
    if hasattr(root, 'messages_popup') and root.messages_popup.winfo_exists():
        root.messages_text_widget.config(state=NORMAL)
        root.messages_text_widget.insert(END, msg + "\n")
        root.messages_text_widget.see(END)
        root.messages_text_widget.config(state=DISABLED)

def show_messages_popup(root, messages):
    popup = Toplevel(root)
    popup.title("Translation Messages")
    popup.geometry("600x400")
    root.messages_popup = popup
    text_widget = Text(popup, wrap=WORD)
    text_widget.pack(fill="both", expand=True)
    root.messages_text_widget = text_widget
    scrollbar = Scrollbar(text_widget)
    scrollbar.pack(side="right", fill="y")
    text_widget.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=text_widget.yview)
    for msg in messages:
        text_widget.insert(END, msg + "\n")
    text_widget.config(state=DISABLED)

# --------------------------
# File Dialog
# --------------------------
def browse_file(file_path_var):
    filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if filename:
        file_path_var.set(filename)

# --------------------------
# Credential Dialog
# --------------------------
def get_credentials(root, engine_selection_var, file_folder=None):
    engine = engine_selection_var.get()
    saved_engine, creds = load_credentials(file_folder) if file_folder else (None, None)
    if saved_engine == engine and creds:
        client_or_keys = verify_and_prepare_client(engine, creds)
        if client_or_keys:
            return client_or_keys, creds
        else:
            messagebox.showwarning("Credentials Invalid", f"Saved credentials for {engine} are invalid. Please enter again.")

    if engine == "openai":
        key = simpledialog.askstring("OpenAI API Key", "Enter your OpenAI API Key:", show="*")
        if not key:
            return None, None
        if not verify_and_prepare_client("openai", {"openai_key": key}):
            messagebox.showerror("Invalid Key", "OpenAI key invalid.")
            return None, None
        save_credentials("openai", {"openai_key": key}, file_folder)
        return verify_and_prepare_client("openai", {"openai_key": key}), {"openai_key": key}

    elif engine == "amazon":
        access = simpledialog.askstring("AWS Access Key", "Enter AWS Access Key ID:")
        secret = simpledialog.askstring("AWS Secret Key", "Enter AWS Secret Access Key:", show="*")
        if not access or not secret:
            return None, None
        if not verify_and_prepare_client("amazon", {"aws_access_key": access, "aws_secret_key": secret}):
            messagebox.showerror("Invalid Key", "AWS credentials invalid.")
            return None, None
        save_credentials("amazon", {"aws_access_key": access, "aws_secret_key": secret}, file_folder)
        return (access, secret), {"aws_access_key": access, "aws_secret_key": secret}

# --------------------------
# Start/Cancel Button Toggle
# --------------------------
def toggle_translation_button(btn, is_running):
    btn.config(text="Cancel Translation" if is_running else "Start Translation")

# --------------------------
# Translation Thread
# --------------------------
def run_translation_thread(root, client_or_keys, creds, input_path, output_path, source_lang, target_langs,
                           status_label, status_text, engine, progress_bar=None, btn=None):
    global cancel_flag_global
    cancel_flag_global = False

    try:
        # Count total text entries
        data = load_json(input_path)
        total_texts = len(collect_translatable_texts(data, source_lang)) * len(target_langs)
        progress_counter = 0

        def status_cb(msg, batch_count=1):
            nonlocal progress_counter
            if cancel_flag_global:
                raise Exception("Translation canceled by user")
            progress_counter += batch_count
            if progress_bar:
                progress_bar["maximum"] = total_texts
                progress_bar["value"] = progress_counter
                progress_bar.update()
            update_status_label(root, status_label, msg, status_text)

        translate(engine, creds, input_path, output_path, source_lang, target_langs, status_callback=status_cb)

        update_status_label(root, status_label, f"✅ Translation complete!\nSaved as:\n{output_path}", status_text)
        messagebox.showinfo("Success", f"Translation complete!\nSaved as:\n{output_path}")

    except Exception as e:
        if str(e) == "Translation canceled by user":
            update_status_label(root, status_label, "❌ Translation canceled.", status_text)
            messagebox.showinfo("Canceled", "Translation canceled by user.")
        else:
            update_status_label(root, status_label, f"❌ Error: {e}", status_text)
            messagebox.showerror("Error", str(e))
    finally:
        if btn:
            toggle_translation_button(btn, False)
        root.protocol("WM_DELETE_WINDOW", root.quit)

def start_or_cancel_translation(root, btn, file_path_var, source_lang_entry, target_langs_entry,
                                engine_var, status_label, status_text, progress_bar):
    global cancel_flag_global
    if btn.cget("text") == "Start Translation":
        input_path = file_path_var.get()
        source_lang = source_lang_entry.get().strip()
        target_langs = [x.strip() for x in target_langs_entry.get().split(",") if x.strip()]
        engine = engine_var.get()
        folder = os.path.dirname(input_path)

        if not os.path.exists(input_path):
            messagebox.showerror("Error", "Please select a valid JSON file.")
            return
        if not target_langs:
            messagebox.showerror("Error", "Enter at least one target language.")
            return

        root.protocol("WM_DELETE_WINDOW", lambda: None)  # disable closing

        client_or_keys, creds = get_credentials(root, engine_var, folder)
        if not client_or_keys:
            root.protocol("WM_DELETE_WINDOW", root.quit)
            return

        output_path = os.path.splitext(input_path)[0] + "_translated.json"

        toggle_translation_button(btn, True)
        progress_bar["value"] = 0
        progress_bar["maximum"] = 1
        progress_bar.update()

        thread = threading.Thread(
            target=run_translation_thread,
            args=(root, client_or_keys, creds, input_path, output_path, source_lang, target_langs,
                  status_label, status_text, engine, progress_bar, btn)
        )
        thread.start()
    else:
        cancel_flag_global = True
