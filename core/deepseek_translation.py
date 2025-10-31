# core/deepseek_translation.py
import os
from typing import Dict, Any, List, Callable, Optional
from .translation_base import BaseTranslationLogic

class DeepSeekTranslationLogic(BaseTranslationLogic):
    """DeepSeek local translation logic"""
    
    def __init__(self):
        self.BATCH_SIZE = 3  # Smaller batches for local processing
        
    def get_name(self) -> str:
        return "deepseek"
    
    def get_description(self) -> str:
        return "DeepSeek Local Translation - Uses local AI models for private, offline translation"
    
    def get_supported_file_types(self) -> List[str]:
        return [".json", ".txt"]
            
    def translate(self, engine: str, creds: Dict, input_path: str, output_path: str, 
                 source_lang: str, target_langs: List[str], 
                 status_callback: Optional[Callable] = None) -> Any:
        
        from engines.deepseek_engine import deepseek_translate_batch, get_deepseek_client
        from utils.file_handlers import load_json, save_json
        
        # Get DeepSeek client
        llm, model_manager = get_deepseek_client()
        
        if not llm.model_loaded:
            if status_callback:
                status_callback("DeepSeek model not loaded. Please load a model first.", batch_count=0)
            return

        data = load_json(input_path)
        
        # Use appropriate collection based on mode (could detect from file structure)
        if self._is_blog_structure(data):
            texts_to_translate = self.collect_text_nodes(data)
        else:
            texts_to_translate = self.collect_translatable_texts(data, source_lang)
            
        if not texts_to_translate:
            if status_callback:
                status_callback("No translatable texts found.", batch_count=0)
            return

        paths, source_texts = zip(*texts_to_translate)
        translated_data = data.copy()

        for target_lang in target_langs:
            if status_callback:
                status_callback(f"Translating to {target_lang} using DeepSeek...", batch_count=0)

            all_translations = []
            for i in range(0, len(source_texts), self.BATCH_SIZE):
                batch = list(source_texts[i:i + self.BATCH_SIZE])
                
                translated_batch = deepseek_translate_batch(llm, batch, source_lang, target_lang)
                all_translations.extend(translated_batch)

                if status_callback:
                    status_callback(f"{len(all_translations)}/{len(source_texts)} texts translated for {target_lang}",
                                    batch_count=len(batch))

            # Apply translations
            translated_data = self.apply_translations(translated_data, all_translations, paths, target_lang, source_lang)

        save_json(translated_data, output_path)
        
        if status_callback:
            status_callback(f"✅ Saved translated file: {output_path}")
    
    def _is_blog_structure(self, data):
        """Detect if JSON has blog structure (type='text' nodes)"""
        # Simple detection logic
        if isinstance(data, dict):
            if data.get("type") == "text":
                return True
            for value in data.values():
                if self._is_blog_structure(value):
                    return True
        elif isinstance(data, list):
            for item in data:
                if self._is_blog_structure(item):
                    return True
        return False
    
    def collect_text_nodes(self, node, path=()):
        """Collect blog-style text nodes"""
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
    
    def collect_translatable_texts(self, node, source_lang, path=()):
        """Collect general translatable texts"""
        texts = []
        if isinstance(node, dict):
            for key, value in node.items():
                if isinstance(value, dict) and source_lang in value and isinstance(value[source_lang], str):
                    texts.append((path + (key,), value[source_lang]))
                elif isinstance(value, (dict, list)):
                    texts.extend(self.collect_translatable_texts(value, source_lang, path + (key,)))
        elif isinstance(node, list):
            for idx, item in enumerate(node):
                texts.extend(self.collect_translatable_texts(item, source_lang, path + (idx,)))
        return texts
    
    def apply_translations(self, node, translations, paths, target_lang, source_lang):
        """Apply translations to JSON structure"""
        for path, text in zip(paths, translations):
            ptr = node
            for key in path[:-1]:
                if isinstance(ptr, list):
                    ptr = ptr[int(key)]
                else:
                    ptr = ptr[key]
            final_key = path[-1]
            
            if isinstance(ptr, dict) and final_key in ptr and isinstance(ptr[final_key], dict):
                if source_lang in ptr[final_key]:
                    ptr[final_key][target_lang] = text
            elif isinstance(ptr, dict) and final_key == "text" and "text" in ptr:
                ptr["text"] = text
            else:
                ptr[final_key] = text
        return node
    