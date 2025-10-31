# model/config.py (Fixed imports)
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# Better Hugging Face import handling
try:
    from huggingface_hub import HfApi, ModelFilter
    HF_AVAILABLE = True
    print("✅ Hugging Face Hub imported successfully")
except ImportError as e:
    HF_AVAILABLE = False
    print(f"⚠️  Hugging Face Hub import failed: {e}")
    print("💡 Try: pip install --upgrade huggingface-hub")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️  requests module not available")

class ModelConfig:
    """Dynamic configuration with direct Hugging Face integration"""
    
    def __init__(self, config_path: str = "data/model_config.json", auto_update: bool = True):
        self.config_path = Path(config_path)
        self.auto_update = auto_update
        self.config_data = self.load_config()
        
        # Check for updates if enabled and HF is available
        if auto_update and HF_AVAILABLE:
            print("🔄 Hugging Face integration enabled - checking for updates...")
            self.check_for_updates()
        else:
            if auto_update:
                print("ℹ️  Hugging Face not available - using local model list")
        
        self._apply_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        if not self.config_path.exists():
            self.create_default_config()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # Add meta info if not present
            if "meta" not in config:
                config["meta"] = {
                    "last_updated": time.time(), 
                    "version": "1.0",
                    "source": "local"
                }
                
            return config
            
        except Exception as e:
            print(f"❌ Error loading config from {self.config_path}: {e}")
            return self.get_default_config()
    
    def check_for_updates(self):
        """Check for updated model lists from Hugging Face"""
        try:
            # Check if we should update (e.g., once per day)
            last_updated = self.config_data.get("meta", {}).get("last_updated", 0)
            current_time = time.time()
            
            # Update if config is older than 1 day or force update
            if current_time - last_updated > 86400:  # 24 hours
                print("🔄 Checking for latest DeepSeek models from Hugging Face...")
                if self.update_from_huggingface():
                    print("✅ Model list updated from Hugging Face!")
                else:
                    print("ℹ️  Using cached model list")
                    
        except Exception as e:
            print(f"⚠️  Could not check for updates: {e}")
    
    def update_from_huggingface(self) -> bool:
        """Fetch latest DeepSeek models directly from Hugging Face"""
        if not HF_AVAILABLE:
            print("  ❌ Hugging Face Hub not available")
            return False
            
        try:
            api = HfApi()
            
            # Get all models from deepseek-ai organization
            print("  📡 Fetching models from deepseek-ai...")
            models = list(api.list_models(
                filter=ModelFilter(author="deepseek-ai"),
                sort="lastModified",
                direction=-1,
                limit=50  # Get latest 50 models
            ))
            
            print(f"  📦 Found {len(models)} models from deepseek-ai")
            
            # Filter and process models
            deepseek_models = {}
            relevant_count = 0
            
            for model in models:
                if self._is_relevant_model(model):
                    model_info = self._process_model_info(model)
                    if model_info:
                        model_key = model.modelId.split('/')[-1]
                        deepseek_models[model_key] = model_info
                        relevant_count += 1
            
            print(f"  ✅ Processed {relevant_count} relevant DeepSeek models")
            
            if deepseek_models:
                # Merge with existing config
                self.merge_with_hf_models(deepseek_models)
                self.config_data["meta"]["last_updated"] = time.time()
                self.config_data["meta"]["source"] = "huggingface"
                self.save_config()
                self._apply_config()
                return True
            else:
                print("  ⚠️  No relevant DeepSeek models found")
                return False
                
        except Exception as e:
            print(f"  ❌ Failed to fetch from Hugging Face: {e}")
            return False
    
    def _is_relevant_model(self, model) -> bool:
        """Check if model is relevant for our translation app"""
        model_name = model.modelId.lower()
        
        # Include relevant model types
        relevant_keywords = [
            'coder', 'llm', 'deepseek', 'chat', 'instruct', 
            'base', 'translation', 'multilingual'
        ]
        
        # Exclude irrelevant models
        exclude_keywords = [
            'vl', 'vision', 'video', 'audio', 'diffusion', 
            'vq', 'clip', 'dpo', 'reward', 'test', 'demo'
        ]
        
        # Check if model has any relevant keywords
        has_relevant = any(keyword in model_name for keyword in relevant_keywords)
        has_excluded = any(keyword in model_name for keyword in exclude_keywords)
        
        return has_relevant and not has_excluded and getattr(model, 'private', False) is False
    
    def _process_model_info(self, model) -> Optional[Dict[str, Any]]:
        """Process model information from Hugging Face"""
        try:
            model_name = model.modelId.split('/')[-1]
            
            # Estimate size based on model ID patterns
            expected_size = self._estimate_model_size(model_name)
            
            # Generate description based on model name
            description = self._generate_model_description(model_name)
            
            # Determine recommendations
            recommended_for = self._get_recommendations_for_model(model_name)
            
            # Estimate parameters
            parameters = self._estimate_parameters(model_name)
            
            # Get tags
            tags = self._get_model_tags(model_name)
            
            model_info = {
                "repo_id": model.modelId,
                "description": description,
                "expected_size": expected_size,
                "recommended_for": recommended_for,
                "parameters": parameters,
                "tags": tags,
                "downloads": getattr(model, 'downloads', 0) or 0,
            }
            
            # Add last modified if available
            if hasattr(model, 'lastModified') and model.lastModified:
                model_info["last_modified"] = model.lastModified.isoformat()
            
            return model_info
            
        except Exception as e:
            print(f"  ⚠️  Could not process model {model.modelId}: {e}")
            return None
    
    def _estimate_model_size(self, model_name: str) -> str:
        """Estimate model size based on name patterns"""
        model_name_lower = model_name.lower()
        
        if '1.3b' in model_name_lower or '1.3' in model_name_lower:
            return "~2.6GB"
        elif '7b' in model_name_lower or '6.7b' in model_name_lower:
            return "~14GB"
        elif '16b' in model_name_lower:
            return "~30GB"
        elif '67b' in model_name_lower:
            return "~130GB"
        elif 'b' in model_name_lower:
            # Extract number of billions
            import re
            match = re.search(r'(\d+)b', model_name_lower)
            if match:
                billions = int(match.group(1))
                return f"~{billions * 2}GB"
        
        return "~10GB"  # Default fallback
    
    def _generate_model_description(self, model_name: str) -> str:
        """Generate human-readable description from model name"""
        model_name_lower = model_name.lower()
        
        descriptions = {
            'coder': "Code generation and translation model",
            'llm': "General language model",
            'chat': "Chat-optimized model for conversation",
            'instruct': "Instruction-tuned model for following directions",
            'base': "Base pre-trained model",
            'v2': "Version 2 with improved capabilities",
            'v3': "Latest version with enhanced performance"
        }
        
        # Build description from components
        parts = []
        if '1.3b' in model_name_lower:
            parts.append("1.3B parameter model")
        elif '7b' in model_name_lower:
            parts.append("7B parameter model") 
        elif '16b' in model_name_lower:
            parts.append("16B parameter model")
        elif '67b' in model_name_lower:
            parts.append("67B parameter model")
        else:
            parts.append("DeepSeek model")
        
        # Add type descriptions
        for key, desc in descriptions.items():
            if key in model_name_lower:
                parts.append(desc)
        
        # Add special capabilities
        if 'coder' in model_name_lower:
            parts.append("excels at code translation")
        if 'chat' in model_name_lower or 'instruct' in model_name_lower:
            parts.append("good for text translation")
        
        return " - ".join(parts)
    
    def _estimate_parameters(self, model_name: str) -> int:
        """Estimate number of parameters"""
        model_name_lower = model_name.lower()
        
        if '1.3b' in model_name_lower:
            return 1_300_000_000
        elif '6.7b' in model_name_lower:
            return 6_700_000_000
        elif '7b' in model_name_lower:
            return 7_000_000_000
        elif '16b' in model_name_lower:
            return 16_000_000_000
        elif '67b' in model_name_lower:
            return 67_000_000_000
        else:
            return 0  # Unknown
    
    def _get_model_tags(self, model_name: str) -> List[str]:
        """Get tags for model categorization"""
        tags = []
        model_name_lower = model_name.lower()
        
        # Size tags
        if '1.3b' in model_name_lower:
            tags.extend(["tiny", "fast", "cpu-friendly"])
        elif '7b' in model_name_lower or '6.7b' in model_name_lower:
            tags.extend(["medium", "balanced", "gpu-recommended"])
        elif '16b' in model_name_lower:
            tags.extend(["large", "high-quality", "gpu-required"])
        elif '67b' in model_name_lower:
            tags.extend(["huge", "best-quality", "server-only"])
        
        # Type tags
        if 'coder' in model_name_lower:
            tags.extend(["code", "programming"])
        if 'llm' in model_name_lower:
            tags.extend(["general", "text"])
        if 'chat' in model_name_lower:
            tags.extend(["chat", "conversation"])
        if 'instruct' in model_name_lower:
            tags.extend(["instruct", "commands"])
        if 'v2' in model_name_lower:
            tags.append("v2")
        if 'v3' in model_name_lower:
            tags.append("v3")
        
        return tags
    
    def _get_recommendations_for_model(self, model_name: str) -> List[str]:
        """Get recommendation categories for model"""
        recommendations = []
        model_name_lower = model_name.lower()
        
        if '1.3b' in model_name_lower:
            recommendations.extend(["translation_cpu", "low_memory", "fastest"])
        elif '7b' in model_name_lower or '6.7b' in model_name_lower:
            recommendations.extend(["translation_gpu_8gb", "balanced"])
        elif '16b' in model_name_lower:
            recommendations.extend(["translation_gpu_16gb", "high_quality"])
        elif '67b' in model_name_lower:
            recommendations.extend(["server", "best_quality"])
        
        if 'coder' in model_name_lower:
            recommendations.append("code_translation")
        if 'chat' in model_name_lower or 'instruct' in model_name_lower:
            recommendations.append("text_translation")
        
        return recommendations
    
    def merge_with_hf_models(self, hf_models: Dict[str, Any]):
        """Merge Hugging Face models with existing config"""
        # Preserve local custom models
        local_models = self.config_data.get("available_models", {})
        custom_models = {name: info for name, info in local_models.items() 
                        if info.get("tags", []) and "custom" in info.get("tags", [])}
        
        # Start with HF models
        merged_models = hf_models.copy()
        
        # Add custom models back
        merged_models.update(custom_models)
        
        # Update the config
        self.config_data["available_models"] = merged_models
        
        # Update recommendations based on new models
        self._update_recommendations()
    
    def _update_recommendations(self):
        """Update recommendations based on current models"""
        recommendations = {
            "translation_cpu": [],
            "translation_gpu_8gb": [], 
            "translation_gpu_16gb": [],
            "best_quality": [],
            "fastest": [],
            "balanced": [],
            "code_translation": [],
            "text_translation": []
        }
        
        for model_name, model_info in self.config_data["available_models"].items():
            model_recs = model_info.get("recommended_for", [])
            for rec in model_recs:
                if rec in recommendations:
                    recommendations[rec].append(model_name)
        
        # Remove empty categories and sort
        self.config_data["recommendations"] = {
            k: sorted(v) for k, v in recommendations.items() if v
        }
    
    def get_deepseek_models_status(self) -> Dict[str, Any]:
        """Get status of DeepSeek model fetching"""
        if not HF_AVAILABLE:
            return {
                "huggingface_available": False,
                "status": "Hugging Face Hub not available"
            }
        
        try:
            api = HfApi()
            models = list(api.list_models(
                filter=ModelFilter(author="deepseek-ai"),
                limit=5
            ))
            
            return {
                "huggingface_available": True,
                "deepseek_models_found": len(models),
                "status": f"Connected - Found {len(models)} DeepSeek models"
            }
        except Exception as e:
            return {
                "huggingface_available": True,
                "status": f"Connection error: {str(e)}"
            }
    
    def create_default_config(self):
        """Create default configuration file"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        default_config = self.get_default_config()
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        print(f"✅ Created default config at {self.config_path}")
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "meta": {
                "version": "1.0", 
                "last_updated": time.time(),
                "source": "local"
            },
            "available_models": {
                "deepseek-coder-1.3b": {
                    "repo_id": "deepseek-ai/DeepSeek-Coder-1.3b",
                    "description": "1.3B params - Fast, good for translation, runs on CPU",
                    "expected_size": "~2.6GB",
                    "recommended_for": ["translation_cpu", "low_memory"],
                    "parameters": 1300000000,
                    "tags": ["fast", "cpu", "lightweight"]
                },
                "deepseek-llm-7b-chat": {
                    "repo_id": "deepseek-ai/DeepSeek-LLM-7B-Chat",
                    "description": "7B params - Better quality, optimized for chat/translation",
                    "expected_size": "~14GB",
                    "recommended_for": ["translation_gpu_8gb", "balanced"],
                    "parameters": 6700000000,
                    "tags": ["balanced", "gpu", "chat"]
                }
            },
            "recommendations": {
                "translation_cpu": ["deepseek-coder-1.3b"],
                "translation_gpu_8gb": ["deepseek-llm-7b-chat", "deepseek-coder-1.3b"]
            },
            "settings": {
                "default_model": "deepseek-llm-7b-chat",
                "models_dir": "models", 
                "cache_dir": "model_cache",
                "device": "auto",
                "load_in_8bit": True,
                "load_in_4bit": False,
                "max_input_length": 2000,
                "max_new_tokens": 1000,
                "batch_size": 2,
                "temperature": 0.3,
                "top_p": 0.9,
                "repetition_penalty": 1.1
            }
        }
    
    def _apply_config(self):
        """Apply configuration to class attributes"""
        # Available models
        self.AVAILABLE_MODELS = {
            name: model["repo_id"] 
            for name, model in self.config_data["available_models"].items()
        }
        
        # Model details  
        self.MODEL_DESCRIPTIONS = {
            name: model["description"]
            for name, model in self.config_data["available_models"].items()
        }
        
        self.MODEL_SIZES = {
            name: model["expected_size"]
            for name, model in self.config_data["available_models"].items()
        }
        
        # Recommendations
        self.RECOMMENDED_MODELS = self.config_data.get("recommendations", {})
        
        # Settings
        settings = self.config_data.get("settings", {})
        self.DEFAULT_MODEL = settings.get("default_model", "deepseek-llm-7b-chat")
        self.MODELS_DIR = Path(settings.get("models_dir", "models"))
        self.CACHE_DIR = Path(settings.get("cache_dir", "model_cache"))
        self.DEVICE = settings.get("device", "auto")
        self.LOAD_IN_8BIT = settings.get("load_in_8bit", True)
        self.LOAD_IN_4BIT = settings.get("load_in_4bit", False)
        self.MAX_INPUT_LENGTH = settings.get("max_input_length", 2000)
        self.MAX_NEW_TOKENS = settings.get("max_new_tokens", 1000)
        self.BATCH_SIZE = settings.get("batch_size", 2)
        self.TEMPERATURE = settings.get("temperature", 0.3)
        self.TOP_P = settings.get("top_p", 0.9)
        self.REPETITION_PENALTY = settings.get("repetition_penalty", 1.1)
    
    def get_model_details(self, model_name: str) -> Dict[str, Any]:
        """Get detailed information about a model"""
        return self.config_data["available_models"].get(model_name, {})
    
    def get_recommendations(self, category: str) -> List[str]:
        """Get recommended models for a category"""
        return self.RECOMMENDED_MODELS.get(category, [])
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Error saving config: {e}")