# translator_logic.py

import json
import copy
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
    if isinstance(content_array, dict):
        if "text" in content_array and isinstance(content_array["text"], str):
            text_value = content_array["text"]
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


def collect_translatable_texts(node, source_lang, path=(), engine="openai"):
    texts = []
    if isinstance(node, dict):
        for key, value in node.items():
            # ✅ FIX #1: Handle nested additionalContent correctly
            if key == "additionalContent" and isinstance(value, dict) and source_lang in value and isinstance(value[source_lang], list):
                for item_idx, item in enumerate(value[source_lang]):
                    texts.extend(
                        collect_texts_from_content_array(
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

        # ✅ FIX #2: prevent language mixing — only update source_lang section
        if isinstance(ptr, dict) and final_key in ptr and isinstance(ptr[final_key], dict):
            if source_lang in ptr[final_key]:
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

def remove_empty_texts(node):
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
        for item in node:
            remove_empty_texts(item)

def translate(engine, creds, input_path, output_path, source_lang, target_langs, status_callback=None):
    data = load_json(input_path)
    # Preserve original English content for safety
    original_en = copy.deepcopy(data)
    texts_to_translate = collect_translatable_texts(data, source_lang, engine=engine)

    if not texts_to_translate:
        if status_callback:
            status_callback("No translatable texts found.", batch_count=0)
        return

    paths, source_texts = zip(*texts_to_translate)
    translated_data = copy.deepcopy(data)

    for target_lang in target_langs:
        if status_callback:
            status_callback(f"Translating to {target_lang}...", batch_count=0)

        all_translations = []

        for i in range(0, len(source_texts), BATCH_SIZE):
            batch_texts = list(source_texts[i:i+BATCH_SIZE])
            if engine == "openai":
                batch_translations = openai_translate_batch(creds["openai_key"], batch_texts, source_lang, target_lang)
            elif engine == "amazon":
                batch_translations = amazon_translate_batch(creds["aws_access_key"], creds["aws_secret_key"],
                                                            batch_texts, source_lang, target_lang)
            else:
                raise ValueError("Unknown translation engine")

            all_translations.extend(batch_translations)
            if status_callback:
                status_callback(f"{len(all_translations)}/{len(source_texts)} texts translated for {target_lang}",
                                batch_count=len(batch_texts))

        # Apply translations back
        translated_data = apply_translations(translated_data, all_translations, paths, target_lang, source_lang)

        # ✅ FIX #3: Clone additionalContent AFTER translations to correct lang arrays
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

        # ✅ Restore original 'en' content to prevent overwriting by last language
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
        save_json(translated_data, output_path)   

        #save_json(translated_data, output_path)


