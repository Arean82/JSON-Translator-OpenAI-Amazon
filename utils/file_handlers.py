# utils/file_handlers.py
import json
import os
from typing import Any, Dict

def load_json(path: str) -> Any:
    """Load JSON file with UTF-8 encoding"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data: Any, path: str):
    """Save JSON file with UTF-8 encoding and proper formatting"""
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def ensure_directory(path: str):
    """Ensure directory exists"""
    os.makedirs(path, exist_ok=True)

def get_output_path(input_path: str, target_lang: str = None, mode: str = "general") -> str:
    """Generate appropriate output path based on mode"""
    base_dir = os.path.dirname(input_path)
    base_name = os.path.basename(input_path)
    name, ext = os.path.splitext(base_name)
    
    if mode == "blog" and target_lang:
        # Blog mode: lang_filename.json in Blog folder
        output_dir = os.path.join(base_dir, "Blog")
        ensure_directory(output_dir)
        return os.path.join(output_dir, f"{target_lang}_{base_name}")
    elif mode == "general":
        # General mode: filename_translated.json
        return os.path.join(base_dir, f"{name}_translated{ext}")
    else:
        # Default fallback
        return os.path.join(base_dir, f"{name}_translated{ext}")
    
    