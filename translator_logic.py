import json
import copy
import os
from translate_openai import openai_translate_batch, verify_openai_key
from translate_aws import amazon_translate_batch, verify_aws_credentials

BATCH_SIZE = 5

# --------------------------
# JSON Helpers
# --------------------------
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def collect_texts_from_content_array(content_array, current_path, texts_output, source_lang, engine):
    """
    Collects 'text' fields inside structured content arrays.
    It skips empty 'text' fields only for Amazon, as it rejects them.
    """
    if isinstance(content_array, dict):
        if "text" in content_array and isinstance(content_array["text"], str):
            text_value = content_array["text"]
            # Keep the check here to skip empty 'text' nodes inside content structures for Amazon
            if engine == "amazon" and not text_value:
                return
            texts_output.append((current_path + ("text",), text_value))
        for key, value in content_array.items():
            if isinstance(value, (dict, list)):
                collect_texts_from_content_array(value, current_path + (key,), texts_output, source_lang, engine)

    elif isinstance(content_array, list):
        for idx, item in enumerate(content_array):
            if isinstance(item, (dict, list)):
                collect_texts_from_content_array(item, current_path + (idx,), texts_output, source_lang, engine)
    return texts_output

# ---

def collect_translatable_texts(node, source_lang, path=(), engine="openai"):
    """
    Collects all language-specific texts (e.g., 'title': {'en': '...'}) and 
    calls helper for nested content. This function now collects ALL paths, 
    including those with empty strings, so the structure is preserved.
    """
    texts = []
    if isinstance(node, dict):
        for key, value in node.items():
            # Handle nested additionalContent correctly
            if key == "additionalContent" and isinstance(value, dict) and source_lang in value and isinstance(value[source_lang], list):
                for item_idx, item in enumerate(value[source_lang]):
                    texts.extend(
                        collect_texts_from_content_array(
                            item,
                            path + (key, source_lang, item_idx),
                            [],
                            source_lang,
                            engine, # Pass engine to helper, which handles its own skipping
                        )
                    )

            # Collect language-specific fields (e.g., "title": {"en": "..."})
            elif isinstance(value, dict) and source_lang in value and isinstance(value[source_lang], str):
                # We collect the path even if the text is empty!
                texts.append((path + (key,), value[source_lang]))
            else:
                texts.extend(collect_translatable_texts(value, source_lang, path + (key,), engine))
    elif isinstance(node, list):
        for idx, item in enumerate(node):
            texts.extend(collect_translatable_texts(item, source_lang, path + (idx,), engine))
    return texts


def apply_translations(node, translations, paths, target_lang, source_lang):
    for path, text in zip(paths, translations):
        ptr = node
        for key in path[:-1]:
            if isinstance(ptr, list):
                ptr = ptr[int(key)]
            else:
                ptr = ptr[key]
        final_key = path[-1]

        # FIX #2: prevent language mixing — only update source_lang section
        if isinstance(ptr, dict) and final_key in ptr and isinstance(ptr[final_key], dict):
            if source_lang in ptr[final_key]:
                # This ensures {"en": "", "ar": ""} structure is created/updated
                ptr[final_key][target_lang] = text
        elif isinstance(ptr, dict) and final_key == "text" and "text" in ptr:
            ptr["text"] = text
        else:
            ptr[final_key] = text
    return node


def verify_and_prepare_client(engine, creds):
    if engine == "openai":
        return verify_openai_key(creds.get("openai_key"))
    elif engine == "amazon":
        return verify_aws_credentials(creds.get("aws_access_key"), creds.get("aws_secret_key"))
    return None

# ---

def remove_empty_texts(node):
    """
    Recursively remove entries where 'text' is an empty or whitespace-only string
    from deeply nested dicts and lists. (The targeted version is kept)
    """
    if isinstance(node, dict):
        keys_to_delete = []
        for k, v in node.items():
            if k == "text" and isinstance(v, str) and not v.strip():
                keys_to_delete.append(k)
            elif isinstance(v, (dict, list)):
                remove_empty_texts(v)
        for k in keys_to_delete:
            del node[k]

    elif isinstance(node, list):
        items_to_remove = []
        for item in node:
            if isinstance(item, dict) and "text" in item and isinstance(item["text"], str) and not item["text"].strip():
                items_to_remove.append(item)
            elif isinstance(item, (dict, list)):
                remove_empty_texts(item)
        for item in items_to_remove:
            node.remove(item)

# ---

def translate(engine, creds, input_path, output_path, source_lang, target_langs, status_callback=None):
    data = load_json(input_path)
    remove_empty_texts(data)  
    original_en = copy.deepcopy(data) 
    
    # 1. Collect ALL translatable texts and their paths
    all_texts_to_translate = collect_translatable_texts(data, source_lang, engine=engine) 
    
    if not all_texts_to_translate:
        if status_callback:
            status_callback("No translatable texts found.", batch_count=0)
        return

    all_paths, all_source_texts = zip(*all_texts_to_translate)
    translated_data = copy.deepcopy(data)

    # 2. Filter out empty texts for the API call (avoid Amazon error)
    paths_for_api = []
    texts_for_api = []
    api_map = {} # Maps API path index back to original full paths index
    
    for i, (path, text) in enumerate(zip(all_paths, all_source_texts)):
        # Only use non-empty strings for the API call
        if text: 
            paths_for_api.append(path)
            texts_for_api.append(text)
            api_map[len(paths_for_api) - 1] = i # Map the API list index back to the full list index

    for target_lang in target_langs:
        if status_callback:
            status_callback(f"Translating to {target_lang}...", batch_count=0)

        all_translations = [] # Stores translations for only the texts sent to the API
        
        # 3. Perform translation only on non-empty texts
        if texts_for_api:
            for i in range(0, len(texts_for_api), BATCH_SIZE):
                batch_texts = list(texts_for_api[i:i+BATCH_SIZE])
                
                if engine == "openai":
                    batch_translations = openai_translate_batch(creds["openai_key"], batch_texts, source_lang, target_lang)
                elif engine == "amazon":
                    batch_translations = amazon_translate_batch(creds["aws_access_key"], creds["aws_secret_key"],
                                                                 batch_texts, source_lang, target_lang)
                else:
                    raise ValueError("Unknown translation engine")

                all_translations.extend(batch_translations)
                if status_callback:
                    status_callback(f"{len(all_translations)}/{len(texts_for_api)} texts translated for {target_lang}",
                                     batch_count=len(batch_texts))
        
        # 4. Recombine: Build the final list of translations (including empty strings)
        final_translations = []
        api_index = 0
        for text in all_source_texts:
            if text:
                # Use the translation from the API
                final_translations.append(all_translations[api_index])
                api_index += 1
            else:
                # Use an empty string for the target language if source was empty
                final_translations.append("") 

        # 5. Apply translations back using ALL paths and the final translations list
        translated_data = apply_translations(translated_data, final_translations, all_paths, target_lang, source_lang)
        
        # FIX #3: Clone additionalContent AFTER translations to correct lang arrays
        def find_and_copy_content(node, source, target):
            if isinstance(node, dict):
                if "additionalContent" in node and isinstance(node["additionalContent"], dict) and source in node["additionalContent"]:
                    node["additionalContent"][target] = copy.deepcopy(node["additionalContent"][source])
                for k, v in node.items():
                    if isinstance(v, (dict, list)):
                        find_and_copy_content(v, source, target)
            elif isinstance(node, list):
                for item in node:
                    find_and_copy_content(item, source, target)

        find_and_copy_content(translated_data, source_lang, target_lang)

        # Restore original 'en' content
        def restore_original_lang(node, backup, lang):
            if isinstance(node, dict) and isinstance(backup, dict):
                for k, v in node.items():
                    if k == "additionalContent" and isinstance(v, dict) and lang in v and isinstance(backup.get("additionalContent", {}).get(lang), list):
                        node["additionalContent"][lang] = copy.deepcopy(backup["additionalContent"][lang])
                    elif isinstance(v, dict) and k in backup:
                        restore_original_lang(v, backup[k], lang)
                    elif isinstance(v, list) and k in backup:
                        for i, item in enumerate(v):
                            if i < len(backup[k]):
                                restore_original_lang(item, backup[k][i], lang)
            elif isinstance(node, list) and isinstance(backup, list):
                for i, item in enumerate(node):
                    if i < len(backup):
                        restore_original_lang(item, backup[i], lang)

        restore_original_lang(translated_data, original_en, source_lang)
        remove_empty_texts(translated_data)
        
        #save_json(translated_data, output_path)
        output_dir = os.path.join(os.path.dirname(output_path), "Non-Blog")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, os.path.basename(output_path))
