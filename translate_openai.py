import json
from openai import OpenAI

def verify_openai_key(key):
    try:
        client = OpenAI(api_key=key)
        _ = client.models.list()
        return client
    except Exception:
        return None

def openai_translate_batch(api_key, texts, source_lang, target_lang):
    if source_lang == target_lang:
        return texts

    client = OpenAI(api_key=api_key)
    prompt = (
        f"Translate the following JSON array of texts from {source_lang} to {target_lang}. "
        "Return a JSON array of same length, preserve quotes and punctuation, human-like style.\n\n"
        f"{json.dumps(texts, ensure_ascii=False)}"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a professional translator."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=4000
    )
    translated_json = response.choices[0].message.content.strip()
    try:
        return json.loads(translated_json)
    except Exception:
        # fallback
        return translated_json.splitlines()[:len(texts)]
