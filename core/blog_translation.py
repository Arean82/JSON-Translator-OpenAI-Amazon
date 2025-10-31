# core/blog_translation.py
import json
import copy
import os
from typing import Dict, Any, List, Callable, Optional
from .translation_base import BaseTranslationLogic

class BlogTranslationLogic(BaseTranslationLogic):
    """Blog-specific translation logic - only translates text nodes with type='text'"""
    
    def __init__(self):
        self.BATCH_SIZE = 10
        
    def get_name(self) -> str:
        return "blog"
    
    def get_description(self) -> str:
        return "Blog Translation - Only translates 'text' fields where type='text', creates separate files per language"
    
    def get_supported_file_types(self) -> List[str]:
        return [".json"]
    
    def translate(self, engine: str, creds: Dict, input_path: str, output_path: str, 
                 source_lang: str, target_langs: List[str], 
                 status_callback: Optional[Callable] = None) -> Any:
        
        # Import engines
        from engines.openai_engine import openai_translate_batch
        from engines.aws_engine import amazon_translate_batch
        from utils.file_handlers import load_json, save_json
        
        # Your existing translator_blog_logic.py integrated here
        data = load_json(input_path)
        original_data = copy.deepcopy(data)

        texts_to_translate = self.collect_text_nodes(data)
        if not texts_to_translate:
            if status_callback:
                status_callback("No valid text nodes found for translation.", batch_count=0)
            return

        paths, source_texts = zip(*texts_to_translate)

        for target_lang in target_langs:
            if status_callback:
                status_callback(f"Translating to {target_lang}...", batch_count=0)

            all_translations = []
            for i in range(0, len(source_texts), self.BATCH_SIZE):
                batch = list(source_texts[i:i + self.BATCH_SIZE])
                if engine == "openai":
                    translated_batch = openai_translate_batch(creds["openai_key"], batch, source_lang, target_lang)
                elif engine == "amazon":
                    translated_batch = amazon_translate_batch(
                        creds["aws_access_key"], creds["aws_secret_key"],
                        batch, source_lang, target_lang
                    )
                else:
                    raise ValueError("Unknown translation engine")

                all_translations.extend(translated_batch)

                if status_callback:
                    status_callback(f"{len(all_translations)}/{len(source_texts)} texts translated for {target_lang}",
                                    batch_count=len(batch))

            translated_data = self.apply_translations(copy.deepcopy(original_data), all_translations, paths)

            # Blog mode output format
            base_name = os.path.basename(input_path)
            output_dir = os.path.join(os.path.dirname(input_path), "Blog")
            os.makedirs(output_dir, exist_ok=True)
            lang_output = os.path.join(output_dir, f"{target_lang}_{base_name}")
            
            save_json(translated_data, lang_output)

            if status_callback:
                status_callback(f"✅ Saved translated file: {lang_output}")
    
    def collect_text_nodes(self, node, path=()):
        """Your existing blog collection function"""
        texts = []
        if isinstance(node, dict):
            if node.get("type") == "text" and "text" in node and isinstance(node["text"], str):
                text_value = node["text"].strip()
                if text_value:
                    texts.append((path + ("text",), text_value))
            for key, value in node.items():
                if isinstance(value, (dict, list)):
                    texts.extend(self.collect_text_nodes(value, path + (key,)))
        elif isinstance(node, list):
            for idx, item in enumerate(node):
                texts.extend(self.collect_text_nodes(item, path + (idx,)))
        return texts
    
    def apply_translations(self, node, translations, paths):
        """Your existing blog application function"""
        for path, translated_text in zip(paths, translations):
            ptr = node
            for key in path[:-1]:
                if isinstance(ptr, list):
                    ptr = ptr[int(key)]
                else:
                    ptr = ptr[key]
            final_key = path[-1]
            ptr[final_key] = translated_text
        return node
    
    