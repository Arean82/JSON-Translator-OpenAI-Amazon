# core/translation_engine.py
from typing import Dict, Any, List, Optional, Callable
from .translation_base import BaseTranslationLogic
from .general_translation import GeneralTranslationLogic
from .blog_translation import BlogTranslationLogic
from .deepseek_translation import DeepSeekTranslationLogic

class TranslationEngine:
    """Main translation orchestrator"""
    
    def __init__(self):
        # Available translation logics
        self.available_logics = {
            "general": GeneralTranslationLogic(),
            "blog": BlogTranslationLogic(),
            "deepseek": DeepSeekTranslationLogic()
        }
        
        # Default logic
        self.current_logic = self.available_logics["general"]
        self.translation_history = []
    
    def switch_logic(self, logic_name: str) -> bool:
        """Switch between translation logics"""
        if logic_name in self.available_logics:
            self.current_logic = self.available_logics[logic_name]
            return True
        return False
    
    def get_available_logics(self) -> Dict[str, str]:
        """Get available logic names and descriptions"""
        return {name: logic.get_description() for name, logic in self.available_logics.items()}
    
    def get_current_logic(self) -> str:
        """Get current logic name"""
        for name, logic in self.available_logics.items():
            if logic == self.current_logic:
                return name
        return "general"
    
    def translate(self, engine: str, creds: Dict, input_path: str, output_path: str,
                 source_lang: str, target_langs: List[str], 
                 status_callback: Optional[Callable] = None) -> Any:
        """Main translation method"""
        return self.current_logic.translate(
            engine, creds, input_path, output_path, source_lang, target_langs, status_callback
        )
    
    def get_translation_history(self) -> List[Dict[str, Any]]:
        """Get translation history"""
        return self.translation_history.copy()
    
    def clear_history(self):
        """Clear translation history"""
        self.translation_history.clear()

        