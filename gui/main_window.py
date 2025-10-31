# gui/main_window.py
import os
import threading
from tkinter import *
from tkinter import ttk, messagebox, filedialog
from typing import Optional

from core.translation_engine import TranslationEngine
from utils.language_manager import get_languages, open_language_popup
from utils.credentials_manager import load_credentials
from utils.file_handlers import get_output_path
from gui.components.progress_manager import ProgressManager
from gui.components.status_display import StatusDisplay

class MainWindow:
    def __init__(self, root, translation_engine: TranslationEngine, selected_engine: str):
        self.root = root
        self.engine = translation_engine
        self.selected_engine = selected_engine
        self.creds = load_credentials().get(selected_engine, {})
        
        self.setup_window()
        self.create_widgets()
        self.setup_bindings()
        
    def setup_window(self):
        self.root.title(f"JSON Translator – {self.selected_engine.capitalize()}")
        self.root.geometry("500x600")
        self.root.minsize(450, 550)
        
        # Center window
        self.root.eval('tk::PlaceWindow . center')
        
    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=BOTH, expand=True)
        
        # Header
        self.create_header(main_frame)
        
        # File selection
        self.create_file_section(main_frame)
        
        # Translation settings
        self.create_settings_section(main_frame)
        
        # Mode selection
        self.create_mode_section(main_frame)
        
        # Progress and status
        self.create_progress_section(main_frame)
        
        # Action buttons
        self.create_action_section(main_frame)
        
        # Status display
        self.create_status_section(main_frame)
        
    def create_header(self, parent):
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=X, pady=(0, 20))
        
        ttk.Label(
            header_frame, 
            text="JSON Translator", 
            font=("Arial", 16, "bold")
        ).pack()
        
        ttk.Label(
            header_frame, 
            text=f"Engine: {self.selected_engine.capitalize()}", 
            foreground="gray"
        ).pack()
        
    def create_file_section(self, parent):
        file_frame = ttk.LabelFrame(parent, text="File Selection", padding="10")
        file_frame.pack(fill=X, pady=(0, 15))
        
        # File path
        ttk.Label(file_frame, text="Source JSON File:").grid(row=0, column=0, sticky=W, pady=(0, 5))
        
        file_input_frame = ttk.Frame(file_frame)
        file_input_frame.grid(row=1, column=0, columnspan=2, sticky=EW, pady=(0, 10))
        file_input_frame.columnconfigure(0, weight=1)
        
        self.file_path_var = StringVar()
        self.file_entry = ttk.Entry(file_input_frame, textvariable=self.file_path_var)
        self.file_entry.grid(row=0, column=0, sticky=EW, padx=(0, 5))
        
        ttk.Button(
            file_input_frame, 
            text="Browse", 
            command=self.browse_file
        ).grid(row=0, column=1)
        
        # Output path preview
        ttk.Label(file_frame, text="Output will be saved in:").grid(row=2, column=0, sticky=W, pady=(0, 5))
        self.output_preview_var = StringVar(value="Select a file to see output path")
        ttk.Label(
            file_frame, 
            textvariable=self.output_preview_var,
            foreground="blue",
            wraplength=400
        ).grid(row=3, column=0, sticky=W)
        
    def create_settings_section(self, parent):
        settings_frame = ttk.LabelFrame(parent, text="Translation Settings", padding="10")
        settings_frame.pack(fill=X, pady=(0, 15))
        
        # Source language
        ttk.Label(settings_frame, text="Source Language:").grid(row=0, column=0, sticky=W, pady=(0, 5))
        self.source_lang_var = StringVar(value="en")
        ttk.Entry(settings_frame, textvariable=self.source_lang_var, width=10).grid(row=0, column=1, sticky=W, pady=(0, 5), padx=(5, 0))
        
        # Target languages
        langs_frame = ttk.Frame(settings_frame)
        langs_frame.grid(row=1, column=0, columnspan=2, sticky=EW, pady=(10, 0))
        
        ttk.Label(langs_frame, text="Target Languages:").pack(side=LEFT)
        
        self.current_langs_var = StringVar(value=", ".join(get_languages()))
        ttk.Label(
            langs_frame, 
            textvariable=self.current_langs_var,
            foreground="blue",
            font=("Arial", 9)
        ).pack(side=LEFT, padx=(5, 10))
        
        ttk.Button(
            langs_frame,
            text="Manage Languages",
            command=self.manage_languages
        ).pack(side=LEFT)
        
    def create_mode_section(self, parent):
        mode_frame = ttk.LabelFrame(parent, text="Translation Mode", padding="10")
        mode_frame.pack(fill=X, pady=(0, 15))
        
        self.mode_var = StringVar(value="general")
        
        mode_selector_frame = ttk.Frame(mode_frame)
        mode_selector_frame.pack(fill=X)
        
        ttk.Radiobutton(
            mode_selector_frame,
            text="General Mode",
            variable=self.mode_var,
            value="general",
            command=self.on_mode_change
        ).pack(side=LEFT, padx=(0, 20))
        
        ttk.Radiobutton(
            mode_selector_frame,
            text="Blog Mode",
            variable=self.mode_var,
            value="blog",
            command=self.on_mode_change
        ).pack(side=LEFT)
        
        # Mode description
        self.mode_desc_var = StringVar()
        self.mode_desc_var.set(self.get_mode_description("general"))
        ttk.Label(
            mode_frame,
            textvariable=self.mode_desc_var,
            foreground="gray",
            wraplength=400,
            font=("Arial", 9)
        ).pack(fill=X, pady=(10, 0))
        
    def create_progress_section(self, parent):
        progress_frame = ttk.LabelFrame(parent, text="Progress", padding="10")
        progress_frame.pack(fill=X, pady=(0, 15))
        
        self.progress_manager = ProgressManager(progress_frame)
        self.progress_manager.pack(fill=X)
        
    def create_action_section(self, parent):
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=X, pady=(0, 15))
        
        self.translate_btn = ttk.Button(
            action_frame,
            text="Start Translation",
            command=self.start_translation,
            style="Accent.TButton"
        )
        self.translate_btn.pack(fill=X)
        
        # DeepSeek model management (only for DeepSeek engine)
        if self.selected_engine == "deepseek":
            model_frame = ttk.Frame(parent)
            model_frame.pack(fill=X, pady=(0, 10))
            
            ttk.Button(
                model_frame,
                text="Manage DeepSeek Models",
                command=self.manage_models
            ).pack(fill=X)
        
    def create_status_section(self, parent):
        self.status_display = StatusDisplay(parent)
        self.status_display.pack(fill=X, pady=(0, 10))
        
    def setup_bindings(self):
        self.file_entry.bind('<KeyRelease>', self.update_output_preview)
        self.file_path_var.trace('w', self.update_output_preview)
        
    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select JSON file",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.file_path_var.set(filename)
            
    def update_output_preview(self, *args):
        file_path = self.file_path_var.get()
        if file_path and os.path.exists(file_path):
            output_path = get_output_path(file_path, mode=self.mode_var.get())
            self.output_preview_var.set(output_path)
        else:
            self.output_preview_var.set("Select a file to see output path")
            
    def manage_languages(self):
        open_language_popup(self.root)
        self.current_langs_var.set(", ".join(get_languages()))
        
    def on_mode_change(self):
        mode = self.mode_var.get()
        self.mode_desc_var.set(self.get_mode_description(mode))
        self.update_output_preview()
        
    def get_mode_description(self, mode):
        descriptions = {
            "general": "General JSON translation - handles complex nested structures with language-specific fields",
            "blog": "Blog translation - only translates 'text' fields where type='text', creates separate files per language"
        }
        return descriptions.get(mode, "")
        
    def start_translation(self):
        input_path = self.file_path_var.get()
        source_lang = self.source_lang_var.get()
        target_langs = get_languages()
        mode = self.mode_var.get()
        
        # Validation
        if not input_path or not os.path.exists(input_path):
            messagebox.showerror("Error", "Please select a valid JSON file.")
            return
            
        if not target_langs:
            messagebox.showerror("Error", "Please add at least one target language.")
            return
            
        # Switch translation logic based on mode
        if not self.engine.switch_logic(mode):
            messagebox.showerror("Error", f"Failed to switch to {mode} mode.")
            return
            
        # Prepare output path
        output_path = get_output_path(input_path, mode=mode)
        
        # Update UI for translation start
        self.translate_btn.config(state=DISABLED, text="Translating...")
        self.progress_manager.start_progress()
        self.status_display.set_status("Starting translation...", "info")
        
        # Start translation in thread
        thread = threading.Thread(
            target=self.run_translation,
            args=(input_path, output_path, source_lang, target_langs)
        )
        thread.daemon = True
        thread.start()
        
    def run_translation(self, input_path, output_path, source_lang, target_langs):
        try:
            def status_callback(message, batch_count=0):
                self.root.after(0, lambda: self.update_translation_status(message, batch_count))
                
            # Perform translation
            result = self.engine.translate(
                engine=self.selected_engine,
                creds=self.creds,
                input_path=input_path,
                output_path=output_path,
                source_lang=source_lang,
                target_langs=target_langs,
                status_callback=status_callback
            )
            
            self.root.after(0, self.translation_complete, True, "Translation completed successfully!")
            
        except Exception as e:
            self.root.after(0, self.translation_complete, False, f"Translation failed: {str(e)}")
            
    def update_translation_status(self, message, batch_count):
        self.status_display.set_status(message, "info")
        if batch_count > 0:
            self.progress_manager.update_progress(batch_count)
            
    def translation_complete(self, success, message):
        self.translate_btn.config(state=NORMAL, text="Start Translation")
        self.progress_manager.complete_progress()
        
        if success:
            self.status_display.set_status(message, "success")
            messagebox.showinfo("Success", message)
        else:
            self.status_display.set_status(message, "error")
            messagebox.showerror("Error", message)
            
    def manage_models(self):
        """Open DeepSeek model management window"""
        if self.selected_engine == "deepseek":
            from gui.deepseek_window import DeepSeekWindow
            model_window = Toplevel(self.root)
            DeepSeekWindow(model_window)
        else:
            messagebox.showinfo("Info", "Model management is only available for DeepSeek engine.")

def main():
    """Test function"""
    root = Tk()
    engine = TranslationEngine()
    app = MainWindow(root, engine, "openai")
    root.mainloop()

if __name__ == "__main__":
    main()

    