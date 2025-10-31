# engines/openai_engine.py
import json
from openai import OpenAI
from typing import List, Optional, Tuple
from utils.logger import get_logger

logger = get_logger()

def verify_openai_key(key: str) -> Tuple[bool, Optional[OpenAI]]:
    """Verify OpenAI API key and return client if valid"""
    try:
        client = OpenAI(api_key=key)
        # Test the key by listing models (lightweight call)
        client.models.list(limit=1)
        logger.log_model_event("OpenAI key verified", "openai")
        return True, client
    except Exception as e:
        logger.log_error(f"OpenAI key verification failed: {str(e)}", "openai")
        return False, None

def openai_translate_batch(api_key: str, texts: List[str], source_lang: str, target_lang: str) -> List[str]:
    """
    Translate batch of texts using OpenAI
    """
    if source_lang == target_lang:
        return texts

    try:
        client = OpenAI(api_key=api_key)
        
        # Filter out empty texts
        non_empty_texts = [text for text in texts if text and text.strip()]
        if not non_empty_texts:
            return [""] * len(texts)
        
        # Build better prompt for translation
        prompt = build_openai_translation_prompt(non_empty_texts, source_lang, target_lang)

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using the more cost-effective model
            messages=[
                {
                    "role": "system", 
                    "content": "You are a professional translator. Return only JSON array of translations."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            temperature=0.3,  # Lower temperature for more consistent translations
            max_tokens=4000,
            response_format={"type": "json_object"}
        )
        
        translated_content = response.choices[0].message.content.strip()
        
        # Parse the response
        try:
            translations_data = json.loads(translated_content)
            translations_list = translations_data.get("translations", [])
            
            # Map back to original positions (including empty texts)
            result = []
            text_index = 0
            for original_text in texts:
                if original_text and original_text.strip():
                    if text_index < len(translations_list):
                        result.append(translations_list[text_index])
                        text_index += 1
                    else:
                        result.append(original_text)  # Fallback
                else:
                    result.append("")
            
            logger.log_translation_batch(1, 1, "openai")  # Single batch for OpenAI
            return result
            
        except json.JSONDecodeError:
            # Fallback: try to parse as plain text
            logger.log_error("OpenAI returned non-JSON response, using fallback", "openai")
            lines = translated_content.split('\n')
            return lines[:len(texts)] if lines else texts
    
    except Exception as e:
        logger.log_error(f"OpenAI translation failed: {str(e)}", "openai")
        # Return original texts as fallback
        return texts

def build_openai_translation_prompt(texts: List[str], source_lang: str, target_lang: str) -> str:
    """Build optimized prompt for OpenAI translation"""
    
    from utils.language_manager import get_language_name
    
    source_name = get_language_name(source_lang)
    target_name = get_language_name(target_lang)
    
    prompt = f"""Translate the following texts from {source_name} to {target_name}.

**Instructions:**
- Return a JSON object with a single key "translations" containing an array of translated texts
- Maintain the exact order of the input texts
- Preserve the original meaning and tone
- Keep proper names, technical terms, and formatting unchanged
- Ensure natural, human-like translations
- For empty input texts, return empty strings

**Input texts (as JSON array):**
{json.dumps(texts, ensure_ascii=False, indent=2)}

**Return format:**
{{"translations": ["translated_text_1", "translated_text_2", ...]}}

**Translations:**
"""
    
    return prompt

def openai_translate_single(api_key: str, text: str, source_lang: str, target_lang: str) -> str:
    """Translate single text using OpenAI"""
    if not text or not text.strip():
        return ""
    
    try:
        client = OpenAI(api_key=api_key)
        
        prompt = f"Translate the following text from {source_lang} to {target_lang}. Provide only the translation:\n\n{text}"
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional translator."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        logger.log_error(f"OpenAI single translation failed: {str(e)}", "openai")
        return text  # Return original text as fallback
    
    