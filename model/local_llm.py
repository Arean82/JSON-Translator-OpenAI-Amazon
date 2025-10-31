# model/local_llm.py
import torch
import logging
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    pipeline
)
from typing import Optional, Dict, Any, List
import gc
import os

from .model_manager import ModelManager
from .config import ModelConfig
from utils.logger import get_logger

logger = get_logger()

class LocalLLM:
    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
        self.config = model_manager.config
        self.pipeline = None
        self.model_loaded = False
        self.current_model_name = None
        
    def load_model(self, model_name: str) -> bool:
        """Load model into memory"""
        try:
            # Cleanup previous model
            self.unload_model()
            
            print(f"🔄 Loading model: {model_name}")
            logger.log_model_event("Loading model", model_name)
            
            model_path = self.model_manager.get_model_path(model_name)
            if not model_path.exists():
                print(f"❌ Model not found locally. Please download {model_name} first.")
                logger.log_error(f"Model not found: {model_name}", "deepseek")
                return False
            
            # Configure quantization for memory efficiency
            quantization_config = None
            if self.config.LOAD_IN_4BIT and torch.cuda.is_available():
                print("🔧 Using 4-bit quantization")
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_use_double_quant=True,
                )
            elif self.config.LOAD_IN_8BIT and torch.cuda.is_available():
                print("🔧 Using 8-bit quantization")
                quantization_config = BitsAndBytesConfig(load_in_8bit=True)
            else:
                print("🔧 Using default precision (no quantization)")
            
            # Determine device
            device = self._determine_device()
            print(f"🖥️  Using device: {device}")
            
            # Load tokenizer
            print("📥 Loading tokenizer...")
            tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True,
                local_files_only=True
            )
            
            # Set padding token if not exists
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            # Load model
            print("📥 Loading model...")
            model_kwargs = {
                "trust_remote_code": True,
                "low_cpu_mem_usage": True,
                "local_files_only": True
            }
            
            if quantization_config:
                model_kwargs["quantization_config"] = quantization_config
                model_kwargs["torch_dtype"] = torch.float16
            else:
                model_kwargs["torch_dtype"] = torch.float16 if torch.cuda.is_available() else torch.float32
            
            if device != "cpu":
                model_kwargs["device_map"] = device
            else:
                model_kwargs["device_map"] = None
                model_kwargs["torch_dtype"] = torch.float32
            
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                **model_kwargs
            )
            
            # Move to device if not using device_map
            if device == "cpu":
                model = model.to(device)
            
            # Create pipeline
            print("🔧 Creating pipeline...")
            self.pipeline = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                device=0 if torch.cuda.is_available() else -1,  # GPU: 0, CPU: -1
            )
            
            self.model_loaded = True
            self.current_model_name = model_name
            self.model_manager.current_model_name = model_name
            
            memory_info = self.get_memory_usage()
            print(f"✅ Model {model_name} loaded successfully!")
            print(f"💾 Memory: {memory_info}")
            logger.log_model_event("Model loaded", model_name, f"on {device}")
            
            return True
            
        except Exception as e:
            error_msg = f"Error loading model {model_name}: {str(e)}"
            print(f"❌ {error_msg}")
            logger.log_error(error_msg, "deepseek")
            self.unload_model()
            return False
    
    def _determine_device(self) -> str:
        """Determine the best device to use"""
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # GB
            print(f"🎯 GPU detected: {gpu_name} ({gpu_memory:.1f}GB)")
            
            if gpu_memory >= 8:  # 8GB+ VRAM
                return "auto"  # Use GPU with automatic device mapping
            else:
                print("⚠️  GPU VRAM may be insufficient, consider using CPU or smaller model")
                return "auto"
        else:
            print("⚠️  No GPU detected, using CPU (slower)")
            return "cpu"
    
    def unload_model(self):
        """Unload model from memory"""
        if self.pipeline:
            try:
                del self.pipeline
                self.pipeline = None
            except:
                pass
        
        self.model_manager.cleanup()
        self.model_loaded = False
        self.current_model_name = None
        
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        print("🧹 Model unloaded from memory")
        logger.log_model_event("Model unloaded", self.current_model_name or "unknown")
    
    def generate_text(self, prompt: str, max_new_tokens: int = 500, temperature: float = 0.3) -> str:
        """Generate text using loaded model"""
        if not self.model_loaded or not self.pipeline:
            raise Exception("No model loaded. Please load a model first.")
        
        try:
            with torch.no_grad():
                # Prepare generation parameters
                generation_config = {
                    "max_new_tokens": max_new_tokens,
                    "temperature": temperature,
                    "do_sample": temperature > 0,
                    "top_p": self.config.TOP_P,
                    "repetition_penalty": self.config.REPETITION_PENALTY,
                    "pad_token_id": self.pipeline.tokenizer.eos_token_id,
                    "eos_token_id": self.pipeline.tokenizer.eos_token_id,
                }
                
                # Generate response
                response = self.pipeline(
                    prompt,
                    **generation_config
                )
                
                generated_text = response[0]['generated_text']
                
                # Remove the prompt from the response
                if generated_text.startswith(prompt):
                    generated_text = generated_text[len(prompt):].strip()
                
                logger.log_model_event("Text generated", self.current_model_name, f"tokens: {max_new_tokens}")
                return generated_text
                
        except Exception as e:
            error_msg = f"Text generation failed: {str(e)}"
            logger.log_error(error_msg, "deepseek")
            raise Exception(error_msg)
    
    def generate_batch(self, prompts: List[str], max_new_tokens: int = 500, temperature: float = 0.3) -> List[str]:
        """Generate text for multiple prompts (batched)"""
        if not self.model_loaded or not self.pipeline:
            raise Exception("No model loaded. Please load a model first.")
        
        results = []
        for i, prompt in enumerate(prompts):
            try:
                result = self.generate_text(prompt, max_new_tokens, temperature)
                results.append(result)
                print(f"✅ Generated {i+1}/{len(prompts)}")
            except Exception as e:
                print(f"❌ Failed to generate for prompt {i+1}: {e}")
                results.append("")  # Return empty string on error
        
        return results
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage information"""
        try:
            if torch.cuda.is_available():
                return {
                    "cuda_allocated": torch.cuda.memory_allocated() / 1024**3,
                    "cuda_reserved": torch.cuda.memory_reserved() / 1024**3,
                    "cuda_max_allocated": torch.cuda.max_memory_allocated() / 1024**3,
                    "device": "cuda",
                    "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "None"
                }
            else:
                import psutil
                process = psutil.Process()
                memory_info = process.memory_info()
                return {
                    "rss_memory": memory_info.rss / 1024**3,  # Resident Set Size in GB
                    "vms_memory": memory_info.vms / 1024**3,  # Virtual Memory Size in GB
                    "device": "cpu"
                }
        except Exception as e:
            return {"device": "unknown", "error": str(e)}
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        if not self.model_loaded:
            return {"model_loaded": False}
        
        memory_info = self.get_memory_usage()
        
        return {
            "model_loaded": True,
            "model_name": self.current_model_name,
            "model_path": str(self.model_manager.get_model_path(self.current_model_name)),
            "memory_usage": memory_info,
            "device": memory_info.get("device", "unknown"),
            "pipeline_ready": self.pipeline is not None
        }
    
    def test_generation(self, test_prompt: str = "Translate 'Hello' to Spanish:") -> str:
        """Test model generation with a simple prompt"""
        if not self.model_loaded:
            return "Model not loaded"
        
        try:
            result = self.generate_text(test_prompt, max_new_tokens=50, temperature=0.1)
            return f"✅ Test successful: {result}"
        except Exception as e:
            return f"❌ Test failed: {str(e)}"
        
        