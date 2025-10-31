# model/model_manager.py
import os
import torch
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from huggingface_hub import snapshot_download
from tqdm import tqdm
import requests

from .config import ModelConfig
from utils.logger import get_logger

logger = get_logger()

class ModelManager:
    def __init__(self, config: ModelConfig):
        self.config = config
        self.loaded_model = None
        self.loaded_tokenizer = None
        self.current_model_name = None
        
        # Create directories
        self.config.MODELS_DIR.mkdir(exist_ok=True)
        self.config.CACHE_DIR.mkdir(exist_ok=True)
        
    def get_model_path(self, model_name: str) -> Path:
        """Get local path for model"""
        return self.config.MODELS_DIR / model_name
    
    def download_model(self, model_name: str) -> Path:
        """Download model from HuggingFace Hub with progress tracking"""
        if model_name not in self.config.AVAILABLE_MODELS:
            raise ValueError(f"Model {model_name} not available. Available: {list(self.config.AVAILABLE_MODELS.keys())}")
        
        repo_id = self.config.AVAILABLE_MODELS[model_name]
        local_path = self.get_model_path(model_name)
        
        if local_path.exists():
            print(f"✅ Model {model_name} already exists at {local_path}")
            return local_path
        
        print(f"⬇️  Downloading {model_name} from {repo_id}...")
        print("This may take a while depending on your internet connection and model size.")
        print("Recommended models for different hardware:")
        print("  • deepseek-coder-1.3b - 2.6GB - Good for CPUs and low-end GPUs")
        print("  • deepseek-llm-7b - 14GB - Requires 8GB+ GPU RAM")
        print("  • deepseek-coder-6.7b - 13GB - Requires 8GB+ GPU RAM")
        
        try:
            # Download with progress bar
            snapshot_download(
                repo_id=repo_id,
                local_dir=local_path,
                local_dir_use_symlinks=False,
                resume_download=True,
                allow_patterns=["*.bin", "*.json", "*.model", "*.py", "tokenizer*", "config.*", "*.txt"],
                ignore_patterns=["*.h5", "*.ot", "*.msgpack"],
            )
            print(f"✅ Model {model_name} downloaded successfully to {local_path}")
            logger.log_model_event("Model downloaded", model_name, f"to {local_path}")
            return local_path
            
        except Exception as e:
            error_msg = f"Failed to download model {model_name}: {str(e)}"
            print(f"❌ {error_msg}")
            logger.log_error(error_msg, "deepseek")
            raise Exception(error_msg)
    
    def get_available_models(self) -> List[str]:
        """Get list of available models (downloaded or downloadable)"""
        available = []
        for model_name, repo_id in self.config.AVAILABLE_MODELS.items():
            model_path = self.get_model_path(model_name)
            if model_path.exists():
                # Calculate model size
                size_gb = self._get_folder_size_gb(model_path)
                available.append(f"{model_name} ({size_gb:.1f}GB - ready)")
            else:
                # Show expected size
                expected_size = self._get_expected_size(model_name)
                available.append(f"{model_name} ({expected_size} - needs download)")
        return available
    
    def _get_folder_size_gb(self, folder_path: Path) -> float:
        """Calculate folder size in GB"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
        return total_size / (1024 ** 3)  # Convert to GB
    
    def _get_expected_size(self, model_name: str) -> str:
        """Get expected download size for model"""
        sizes = {
            "deepseek-coder-1.3b": "~2.6GB",
            "deepseek-llm-7b": "~14GB", 
            "deepseek-coder-6.7b": "~13GB"
        }
        return sizes.get(model_name, "unknown size")
    
    def get_downloaded_models(self) -> List[str]:
        """Get list of already downloaded models"""
        downloaded = []
        for model_name in self.config.AVAILABLE_MODELS.keys():
            model_path = self.get_model_path(model_name)
            if model_path.exists():
                downloaded.append(model_name)
        return downloaded
    
    def cleanup(self):
        """Clean up model from memory"""
        if self.loaded_model:
            del self.loaded_model
            self.loaded_model = None
        
        if self.loaded_tokenizer:
            del self.loaded_tokenizer
            self.loaded_tokenizer = None
            
        self.current_model_name = None
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    def check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space"""
        try:
            import shutil
            total, used, free = shutil.disk_usage(self.config.MODELS_DIR)
            return {
                "total_gb": total / (1024**3),
                "used_gb": used / (1024**3),
                "free_gb": free / (1024**3)
            }
        except:
            return {"error": "Could not check disk space"}
        
    def _get_expected_size(self, model_name: str) -> str:
        """Get expected download size for model"""
        sizes = {
            "deepseek-coder-1.3b": "~2.6GB",
            "deepseek-llm-7b-chat": "~14GB",
            "deepseek-coder-v2-base": "~30GB", 
            "deepseek-coder-v2-instruct": "~30GB",
            "deepseek-llm-67b-chat": "~130GB",
            "deepseek-coder-v2-large-base": "~30GB",
            "deepseek-coder-v2-large-instruct": "~30GB",
        }
        return sizes.get(model_name, "unknown size")


        