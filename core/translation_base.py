# core/translation_base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable

class BaseTranslationLogic(ABC):
    """Base class for all translation logics"""
    
    @abstractmethod
    def translate(self, engine: str, creds: Dict, input_path: str, output_path: str, 
                 source_lang: str, target_langs: List[str], 
                 status_callback: Optional[Callable] = None) -> Any:
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        pass
    
    @abstractmethod
    def get_supported_file_types(self) -> List[str]:
        pass

    