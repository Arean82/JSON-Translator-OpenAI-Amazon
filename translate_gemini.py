# translate_gemini.py

import google.generativeai as genai
from typing import List
import time


# --------------------------
# Verify Gemini API Key
# --------------------------
def verify_gemini_key(api_key: str) -> bool:
    try:
        genai.configure(api_key=api_key)
        # Use a minimal generate_content call instead of get_model for validation
        model = genai.GenerativeModel("gemini-1.5-flash")
        model.generate_content("test", max_output_tokens=1) # Minimal, fast request
        return True
    except Exception as e:
        # This will catch all API-related failures (invalid key, etc.)
        print(f"[Gemini] API Key verification failed: {e}")
        return False
    


# --------------------------
# Translate Batch
# --------------------------
def gemini_translate_batch(api_key: str, texts: List[str], source_lang: str, target_lang: str) -> List[str]:
    """
    Translate a list of texts using Gemini.
    Mimics openai_translate_batch behavior.
    """
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel("gemini-1.5-flash")

    translations = []
    for text in texts:
        try:
            if not text.strip():
                translations.append("")
                continue

            prompt = (
                f"Translate the following text from {source_lang} to {target_lang}. "
                "Preserve formatting and meaning. Do not add explanations or notes.\n\n"
                f"Text: {text}"
            )

            response = model.generate_content(prompt)
            translated_text = response.text.strip() if response and response.text else ""

            # Gemini sometimes outputs language names — clean up
            if translated_text.lower().startswith(("translation:", "translated:")):
                translated_text = translated_text.split(":", 1)[1].strip()

            translations.append(translated_text)

            # Avoid hitting rate limits for large batches
            time.sleep(0.3)

        except Exception as e:
            print(f"[Gemini] Error translating text: {e}")
            translations.append("")

    return translations
