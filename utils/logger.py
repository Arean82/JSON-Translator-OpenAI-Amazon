# utils/logger.py
import logging
import os
from datetime import datetime
from typing import Optional

class TranslationLogger:
    """Logging utility for translation operations"""
    
    def __init__(self, log_file: Optional[str] = None):
        self.log_file = log_file or self._get_default_log_path()
        self._setup_logging()
    
    def _get_default_log_path(self) -> str:
        """Get default log file path"""
        log_dir = os.path.join("data", "logs")
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(log_dir, f"translation_{timestamp}.log")
    
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file, encoding='utf-8'),
                logging.StreamHandler()  # Also print to console
            ]
        )
        self.logger = logging.getLogger('TranslationApp')
    
    def log_translation_start(self, engine: str, source_lang: str, target_langs: list, input_file: str):
        """Log translation start"""
        self.logger.info(f"Translation started - Engine: {engine}, Source: {source_lang}, "
                        f"Targets: {target_langs}, Input: {input_file}")
    
    def log_translation_batch(self, batch_num: int, total_batches: int, engine: str):
        """Log batch translation progress"""
        self.logger.info(f"Batch {batch_num}/{total_batches} processed - Engine: {engine}")
    
    def log_translation_complete(self, output_file: str, total_texts: int):
        """Log translation completion"""
        self.logger.info(f"Translation completed - Output: {output_file}, Texts: {total_texts}")
    
    def log_error(self, error_msg: str, engine: str):
        """Log error"""
        self.logger.error(f"Translation error - Engine: {engine}, Error: {error_msg}")
    
    def log_model_event(self, event: str, model_name: str, details: str = ""):
        """Log model-related events"""
        self.logger.info(f"Model event - {event}: {model_name} {details}")
    
    def get_log_content(self) -> str:
        """Get log file content"""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return "No log content available"

# Global logger instance
_translation_logger = None

def get_logger() -> TranslationLogger:
    """Get global logger instance"""
    global _translation_logger
    if _translation_logger is None:
        _translation_logger = TranslationLogger()
    return _translation_logger

