# translator_blog_logic.py
# ---------------------------------------
# Blog Mode Translation Logic
# Translates only "text" fields where type="text"
# Creates separate output files per language.
# ---------------------------------------

import json
import copy
import os
from translate_openai import openai_translate_batch, verify_openai_key
from translate_aws import amazon_translate_batch, verify_aws_credentials

BATCH_SIZE = 10  # Blog content is usually longer, so use slightly larger batches


# --------------------------
# JSON Helpers
# --------------------------
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# --------------------------
# Collect text for translation
# --------------------------
def collect_text_nodes(node, path=()):
    """Collect only text nodes where type == 'text'."""
    texts = []
    if isinstance(node, dict):
        # Only pick up "text" when this dict represents a text node
        if node.get("type") == "text" and "text" in node and isinstance(node["text"], str):
            text_value = node["text"].strip()
            if text_value:  # avoid empty strings
                texts.append((path + ("text",), text_value))
        for key, value in node.items():
            if isinstance(value, (dict, list)):
                texts.extend(collect_text_nodes(value, path + (key,)))
    elif isinstance(node, list):
        for idx, item in enumerate(node):
            texts.extend(collect_text_nodes(item, path + (idx,)))
    return texts


# --------------------------
# Apply Translations
# --------------------------
def apply_translations(node, translations, paths):
    """Apply translated text back to JSON structure."""
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


# --------------------------
# Verify Client Credentials
# --------------------------
def verify_and_prepare_client(engine, creds):
    if engine == "openai":
        return verify_openai_key(creds.get("openai_key"))
    elif engine == "amazon":
        return verify_aws_credentials(creds.get("aws_access_key"), creds.get("aws_secret_key"))
    return None


# --------------------------
# Translation Entry Function
# --------------------------
def translate(engine, creds, input_path, output_path, source_lang, target_langs, status_callback=None):
    data = load_json(input_path)
    original_data = copy.deepcopy(data)

    # Collect texts
    texts_to_translate = collect_text_nodes(data)
    if not texts_to_translate:
        if status_callback:
            status_callback("No valid text nodes found for translation.", batch_count=0)
        return

    paths, source_texts = zip(*texts_to_translate)

    # Translate per target language
    for target_lang in target_langs:
        if status_callback:
            status_callback(f"Translating to {target_lang}...", batch_count=0)

        all_translations = []
        for i in range(0, len(source_texts), BATCH_SIZE):
            batch = list(source_texts[i:i + BATCH_SIZE])
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

        translated_data = apply_translations(copy.deepcopy(original_data), all_translations, paths)

        # ✅ Blog mode output format: <lang>_<filename>.json
        base_name = os.path.basename(input_path)
        #lang_output = os.path.join(os.path.dirname(input_path), f"{target_lang}_{base_name}")
        
        # ✅ Save inside Blog folder
        output_dir = os.path.join(os.path.dirname(input_path), "Blog")
        os.makedirs(output_dir, exist_ok=True)

        lang_output = os.path.join(output_dir, f"{target_lang}_{base_name}")

        
        save_json(translated_data, lang_output)

        if status_callback:
            status_callback(f"✅ Saved translated file: {lang_output}")

