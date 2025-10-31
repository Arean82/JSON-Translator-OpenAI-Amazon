# engines/deepseek_engine.py
import re
import json
from typing import List, Optional, Tuple, Dict, Any

# Fix the import path
from model.local_llm import LocalLLM
from model.model_manager import ModelManager
from model.config import ModelConfig


def verify_deepseek_credentials():
    """Verify DeepSeek is available - always returns True for local"""
    return True

def deepseek_translate_batch(llm: LocalLLM, texts: List[str], source_lang: str, target_lang: str) -> List[str]:
    """
    Translate batch of texts using DeepSeek local model
    """
    if not llm.model_loaded:
        raise Exception("DeepSeek model not loaded")
    
    translations = []
    
    for text in texts:
        # Build translation prompt
        prompt = build_translation_prompt(text, source_lang, target_lang)
        
        # Generate translation
        translation = llm.generate_text(
            prompt, 
            max_new_tokens=1000,
            temperature=0.3
        )
        
        # Clean up the translation
        cleaned_translation = clean_translation_output(translation)
        translations.append(cleaned_translation)
    
    return translations

def build_translation_prompt(text: str, source_lang: str, target_lang: str) -> str:
    """Build prompt for translation"""
    
    # Load language mapping
    from utils.language_manager import get_language_name
    
    source_name = get_language_name(source_lang)
    target_name = get_language_name(target_lang)
    
    prompt = f"""Translate the following text from {source_name} to {target_name}. 
Provide only the translation without any additional explanations or notes.

Source text: {text}

Translation:"""
    
    return prompt

def clean_translation_output(translation: str) -> str:
    """Clean up translation output"""
    # Remove common prefixes and extra text
    patterns = [
        r'^(Translation|Translated text|Result):\s*',
        r'^["\'](.*)["\']$',
    ]
    
    for pattern in patterns:
        match = re.match(pattern, translation.strip(), re.IGNORECASE)
        if match:
            if match.groups():
                translation = match.group(1)
            else:
                translation = re.sub(pattern, '', translation, flags=re.IGNORECASE)
    
    return translation.strip()

# Singleton instances
_deepseek_llm = None
_deepseek_model_manager = None

def get_deepseek_client():
    """Get or create DeepSeek client instance"""
    global _deepseek_llm, _deepseek_model_manager
    
    if _deepseek_llm is None:
        _deepseek_model_manager = ModelManager(ModelConfig)
        _deepseek_llm = LocalLLM(_deepseek_model_manager)
    
    return _deepseek_llm, _deepseek_model_manager

def load_deepseek_model(model_name: str = "deepseek-coder-1.3b") -> bool:
    """Load specific DeepSeek model"""
    llm, manager = get_deepseek_client()
    return llm.load_model(model_name)

def unload_deepseek_model():
    """Unload DeepSeek model from memory"""
    global _deepseek_llm
    if _deepseek_llm:
        _deepseek_llm.unload_model()

        