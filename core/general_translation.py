# core/general_translation.py
import json
import copy
import os
from typing import Dict, Any, List, Callable, Optional
from .translation_base import BaseTranslationLogic

class GeneralTranslationLogic(BaseTranslationLogic):
    """General JSON translation logic - handles complex nested structures"""
    
    def __init__(self):
        self.BATCH_SIZE = 5
        
    def get_name(self) -> str:
        return "general"
    
    def get_description(self) -> str:
        return "General JSON Translation - Handles complex nested structures with language-specific fields"
    
    def get_supported_file_types(self) -> List[str]:
        return [".json"]
    
    # In core/general_translation.py - update the translate method signature
    def translate(self, engine: str, creds: Dict, input_path: str, output_path: str, 
                  source_lang: str, target_langs: List[str], 
                  status_callback: Optional[Callable] = None) -> Any:

        # Import your existing logic
        from engines.openai_engine import openai_translate_batch, verify_openai_key
        from engines.aws_engine import amazon_translate_batch, verify_aws_credentials
        from utils.file_handlers import load_json, save_json
        
        # Your existing translator_logic.py integrated here
        data = load_json(input_path)
        self.remove_empty_texts(data)
        original_en = copy.deepcopy(data)

        all_texts_to_translate = self.collect_translatable_texts(data, source_lang, engine=engine)
        if not all_texts_to_translate:
            if status_callback:
                status_callback("No translatable texts found.", batch_count=0)
            return

        all_paths, all_source_texts = zip(*all_texts_to_translate)
        translated_data = copy.deepcopy(data)

        # Filter out empty texts for API calls
        paths_for_api = []
        texts_for_api = []
        api_map = {}

        for i, (path, text) in enumerate(zip(all_paths, all_source_texts)):
            if text:
                paths_for_api.append(path)
                texts_for_api.append(text)
                api_map[len(paths_for_api) - 1] = i

        for target_lang in target_langs:
            if status_callback:
                status_callback(f"Translating to {target_lang}...", batch_count=0)

            all_translations = []

            if texts_for_api:
                for i in range(0, len(texts_for_api), self.BATCH_SIZE):
                    batch_texts = list(texts_for_api[i:i + self.BATCH_SIZE])

                    if engine == "openai":
                        batch_translations = openai_translate_batch(
                            creds["openai_key"], batch_texts, source_lang, target_lang
                        )
                    elif engine == "amazon":
                        batch_translations = amazon_translate_batch(
                            creds["aws_access_key"], creds["aws_secret_key"],
                            batch_texts, source_lang, target_lang
                        )
                    else:
                        raise ValueError("Unknown translation engine")

                    all_translations.extend(batch_translations)
                    if status_callback:
                        status_callback(
                            f"{len(all_translations)}/{len(texts_for_api)} texts translated for {target_lang}",
                            batch_count=len(batch_texts)
                        )

            # Apply translations and other logic from your original file
            # ... (rest of your translator_logic.py logic)
            
        return translated_data
    
    # Your existing helper methods
    def collect_texts_from_content_array(self, content_array, current_path, texts_output, source_lang, engine):
        """Your existing function"""
        if isinstance(content_array, dict):
            if "text" in content_array and isinstance(content_array["text"], str):
                text_value = content_array["text"]
                if engine == "amazon" and not text_value:
                    return
                texts_output.append((current_path + ("text",), text_value))
            for key, value in content_array.items():
                if isinstance(value, (dict, list)):
                    self.collect_texts_from_content_array(value, current_path + (key,), texts_output, source_lang, engine)
        elif isinstance(content_array, list):
            for idx, item in enumerate(content_array):
                if isinstance(item, (dict, list)):
                    self.collect_texts_from_content_array(item, current_path + (idx,), texts_output, source_lang, engine)
        return texts_output
    
    def collect_translatable_texts(self, node, source_lang, path=(), engine="openai"):
        """Your existing function"""
        texts = []
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "additionalContent" and isinstance(value, dict) and source_lang in value and isinstance(value[source_lang], list):
                    for item_idx, item in enumerate(value[source_lang]):
                        texts.extend(
                            self.collect_texts_from_content_array(
                                item,
                                path + (key, source_lang, item_idx),
                                [],
                                source_lang,
                                engine,
                            )
                        )
                elif isinstance(value, dict) and source_lang in value and isinstance(value[source_lang], str):
                    texts.append((path + (key,), value[source_lang]))
                else:
                    texts.extend(self.collect_translatable_texts(value, source_lang, path + (key,), engine))
        elif isinstance(node, list):
            for idx, item in enumerate(node):
                texts.extend(self.collect_translatable_texts(item, source_lang, path + (idx,), engine))
        return texts
    
    def remove_empty_texts(self, node):
        """Your existing function"""
        if isinstance(node, dict):
            keys_to_delete = []
            for k, v in node.items():
                if k == "text" and isinstance(v, str) and not v.strip():
                    keys_to_delete.append(k)
                elif isinstance(v, (dict, list)):
                    self.remove_empty_texts(v)
            for k in keys_to_delete:
                del node[k]
        elif isinstance(node, list):
            items_to_remove = []
            for item in node:
                if isinstance(item, dict) and "text" in item and isinstance(item["text"], str) and not item["text"].strip():
                    items_to_remove.append(item)
                elif isinstance(item, (dict, list)):
                    self.remove_empty_texts(item)
            for item in items_to_remove:
                node.remove(item)
    
                