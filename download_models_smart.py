# download_models_smart.py
import os
import sys
import time
import json
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from model.model_manager import ModelManager
from model.config import ModelConfig

class SmartDownloadManager:
    def __init__(self, auto_update: bool = True):
        self.auto_update = auto_update
        self.config = ModelConfig(auto_update=auto_update)
        self.manager = ModelManager(self.config)
        self.local_cache_file = Path("data") / "model_cache.json"
        self.local_cache = self.load_local_cache()

    def check_fresh_model_list(self):
        """Ensure we have the latest model list from Hugging Face"""
        print("🔄 Checking Hugging Face for latest DeepSeek models...")
        
        # Show HF status
        hf_status = self.config.get_deepseek_models_status()
        if hf_status.get("huggingface_available", False):
            if "deepseek_models_found" in hf_status:
                print(f"  ✅ Connected to Hugging Face - Found {hf_status['deepseek_models_found']}+ DeepSeek models")
            else:
                print(f"  ⚠️  Hugging Face: {hf_status.get('status', 'unknown')}")
        else:
            print("  ❌ Hugging Face Hub not available - using local model list")
            print("  💡 Install: pip install huggingface-hub")
        
        # Update local cache with current model status
        self.update_local_cache()
        
        return True

    def show_model_list_with_source(self):
        """Show model list with source information"""
        print("\n📋 DeepSeek Models (Direct from Hugging Face):")
        print("=" * 90)
        
        model_names = list(self.config.AVAILABLE_MODELS.keys())
        
        # Show source info
        meta = self.config.config_data.get("meta", {})
        source = meta.get("source", "local")
        last_updated = meta.get("last_updated", 0)
        
        if source == "huggingface":
            source_info = "🔄 Live from Hugging Face"
        else:
            source_info = "💾 Local cache"
            
        if last_updated:
            last_updated_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(last_updated))
            print(f"📅 {source_info} | Last updated: {last_updated_str}")
        else:
            print(f"📅 {source_info}")
        
        print()
        
        if not model_names:
            print("❌ No DeepSeek models found!")
            return
        
        for i, model_name in enumerate(model_names, 1):
            status = self.get_model_status(model_name)
            description = status["description"]
            expected_size = status["expected_size"]
            parameters = status.get("parameters", 0)
            downloads = status.get("downloads", 0)
            
            # Format parameters
            if parameters >= 1_000_000_000:
                param_str = f"{parameters/1_000_000_000:.1f}B"
            elif parameters >= 1_000_000:
                param_str = f"{parameters/1_000_000:.0f}M"
            else:
                param_str = "Unknown"
            
            # Status indicator
            if status["status"] == "downloaded":
                status_indicator = "✅"
                size_info = f"{status['size_gb']:.1f}GB (downloaded)"
            else:
                status_indicator = "⬇️ "
                size_info = f"{expected_size} (to download)"
            
            # Download count if available
            download_info = f" | 📥 {downloads:,}" if downloads else ""
            
            print(f"{i:2d}. {status_indicator} {model_name}")
            print(f"    📏 Size: {size_info} | 🧠 Params: {param_str}{download_info}")
            print(f"    📝 {description}")
            
            # Show tags if available
            tags = status.get("tags", [])
            if tags:
                print(f"    🏷️  Tags: {', '.join(tags)}")
            print()
   
    def force_huggingface_update(self):
        """Force update from Hugging Face"""
        print("🔄 Fetching latest models from Hugging Face...")
        success = self.config.update_from_huggingface()
        if success:
            print("✅ Model list updated from Hugging Face!")
            # Reinitialize manager with new config
            self.manager = ModelManager(self.config)
        else:
            print("❌ Failed to update from Hugging Face.")
        return success

    def load_local_cache(self):
        """Load local model cache"""
        if self.local_cache_file.exists():
            try:
                with open(self.local_cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"downloaded_models": {}, "last_checked": None}
    
    def save_local_cache(self):
        """Save local model cache"""
        self.local_cache_file.parent.mkdir(exist_ok=True)
        with open(self.local_cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.local_cache, f, indent=2, ensure_ascii=False)
    
    def update_local_cache(self):
        """Update local cache with current model status"""
        downloaded_models = self.manager.get_downloaded_models()
        
        for model_name in self.config.AVAILABLE_MODELS.keys():
            model_path = self.manager.get_model_path(model_name)
            if model_name in downloaded_models and model_path.exists():
                # Calculate actual size
                size_gb = self.manager._get_folder_size_gb(model_path)
                model_details = self.config.get_model_details(model_name)
                
                self.local_cache["downloaded_models"][model_name] = {
                    "status": "downloaded",
                    "size_gb": round(size_gb, 1),
                    "path": str(model_path),
                    "last_verified": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "description": model_details.get("description", ""),
                    "parameters": model_details.get("parameters", 0),
                    "tags": model_details.get("tags", [])
                }
            else:
                # Mark as not downloaded or update status
                if model_name in self.local_cache["downloaded_models"]:
                    self.local_cache["downloaded_models"][model_name]["status"] = "not_downloaded"
        
        self.local_cache["last_checked"] = time.strftime("%Y-%m-%d %H:%M:%S")
        self.save_local_cache()
    
    def scan_local_models(self):
        """Scan and verify all local models"""
        print("🔍 Scanning local models...")
        downloaded_models = self.manager.get_downloaded_models()
        
        if downloaded_models:
            print("✅ Found downloaded models:")
            for model in downloaded_models:
                model_path = self.manager.get_model_path(model)
                size_gb = self.manager._get_folder_size_gb(model_path)
                model_details = self.config.get_model_details(model)
                description = model_details.get("description", "No description")
                print(f"   • {model} ({size_gb:.1f}GB) - {description}")
        else:
            print("❌ No models downloaded yet.")
        
        return downloaded_models
    
    def get_model_status(self, model_name):
        """Get detailed status of a model"""
        model_path = self.manager.get_model_path(model_name)
        model_details = self.config.get_model_details(model_name)
        
        if model_path.exists():
            size_gb = self.manager._get_folder_size_gb(model_path)
            return {
                "status": "downloaded",
                "size_gb": size_gb,
                "path": str(model_path),
                "description": model_details.get("description", ""),
                "expected_size": model_details.get("expected_size", "Unknown"),
                "parameters": model_details.get("parameters", 0),
                "tags": model_details.get("tags", [])
            }
        else:
            return {
                "status": "not_downloaded", 
                "description": model_details.get("description", ""),
                "expected_size": model_details.get("expected_size", "Unknown"),
                "parameters": model_details.get("parameters", 0),
                "tags": model_details.get("tags", [])
            }
    
    def print_recommendations(self):
        """Print hardware recommendations"""
        print("\n💡 Hardware Recommendations:")
        print("┌─────────────────┬─────────────────┬─────────────────────────┐")
        print("│     Hardware    │     RAM/VRAM    │   Recommended Models    │")
        print("├─────────────────┼─────────────────┼─────────────────────────┤")
        
        recommendations = [
            ("CPU / Low-end", "8GB+ RAM", "deepseek-coder-1.3b"),
            ("Mid-range GPU", "8-16GB VRAM", "deepseek-llm-7b-chat"),
            ("High-end GPU", "16GB+ VRAM", "deepseek-coder-v2-*"),
            ("Server GPU", "40GB+ VRAM", "deepseek-llm-67b-chat"),
        ]
        
        for hw, ram, model in recommendations:
            print(f"│ {hw:15} │ {ram:15} │ {model:23} │")
        
        print("└─────────────────┴─────────────────┴─────────────────────────┘")
    
    def print_model_list(self):
        """Print available models with detailed status"""
        print("\n📋 Available Models:")
        print("=" * 90)
        
        model_names = list(self.config.AVAILABLE_MODELS.keys())
        
        for i, model_name in enumerate(model_names, 1):
            status = self.get_model_status(model_name)
            description = status["description"]
            expected_size = status["expected_size"]
            parameters = status.get("parameters", 0)
            
            # Format parameters
            if parameters >= 1_000_000_000:
                param_str = f"{parameters/1_000_000_000:.1f}B"
            elif parameters >= 1_000_000:
                param_str = f"{parameters/1_000_000:.0f}M"
            else:
                param_str = f"{parameters}"
            
            # Status indicator
            if status["status"] == "downloaded":
                status_indicator = "✅"
                size_info = f"{status['size_gb']:.1f}GB (downloaded)"
            else:
                status_indicator = "⬇️ "
                size_info = f"{expected_size} (to download)"
            
            print(f"{i:2d}. {status_indicator} {model_name}")
            print(f"    📏 Size: {size_info} | 🧠 Params: {param_str}")
            print(f"    📝 {description}")
            
            # Show tags if available
            tags = status.get("tags", [])
            if tags:
                print(f"    🏷️  Tags: {', '.join(tags)}")
            print()
    
    def download_model_interactive(self, model_name):
        """Download model with interactive feedback"""
        status = self.get_model_status(model_name)
        
        if status["status"] == "downloaded":
            print(f"✅ {model_name} is already downloaded!")
            print(f"📍 Location: {status['path']}")
            return True
        
        print(f"\n📥 Preparing to download: {model_name}")
        print(f"📏 Expected size: {status['expected_size']}")
        print(f"📝 {status['description']}")
        print("⏰ This may take a while depending on your internet speed...")
        
        # Confirm download
        confirm = input("\nContinue with download? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ Download cancelled.")
            return False
        
        print(f"\n⬇️  Downloading {model_name}...")
        print("💡 Tip: This uses the Hugging Face Hub library for reliable downloads.")
        print("   If it fails, it will resume automatically when you try again.")
        print("   Press Ctrl+C to cancel at any time.\n")
        
        start_time = time.time()
        
        try:
            model_path = self.manager.download_model(model_name)
            download_time = time.time() - start_time
            
            # Verify download
            new_status = self.get_model_status(model_name)
            if new_status["status"] == "downloaded":
                print(f"\n🎉 Success! Model downloaded in {download_time:.1f} seconds")
                print(f"📍 Location: {model_path}")
                
                # Update local cache
                self.update_local_cache()
                
                return True
            else:
                print("❌ Download completed but verification failed.")
                return False
                
        except KeyboardInterrupt:
            print(f"\n\n❌ Download cancelled by user.")
            return False
        except Exception as e:
            print(f"\n❌ Download failed: {e}")
            print("💡 Try again later or check your internet connection.")
            return False

    def main_menu(self):
        """Main interactive menu with Hugging Face integration"""
        while True:
            print("\n" + "="*60)
            print("🚀 DeepSeek Model Manager (Direct from Hugging Face)")
            print("="*60)
            
            # Always check for fresh data before showing menu
            self.check_fresh_model_list()
            
            # Show current local models
            self.scan_local_models()
            self.print_recommendations()
            self.show_model_list_with_source()
            
            print("Options:")
            print("  1-9 - Download/Manage specific model") 
            print("  u   - Force update from Hugging Face")
            print("  s   - Scan local models again")
            print("  h   - Show Hugging Face status")
            print("  q   - Quit")
            
            choice = input("\nEnter your choice: ").strip().lower()
            
            if choice == 'q':
                print("👋 Goodbye!")
                break
            elif choice == 'u':
                self.force_huggingface_update()
                continue
            elif choice == 's':
                self.scan_local_models()
                continue
            elif choice == 'h':
                self.show_huggingface_status()
                continue
            else:
                try:
                    choice_num = int(choice)
                    model_names = list(self.config.AVAILABLE_MODELS.keys())
                    
                    if 1 <= choice_num <= len(model_names):
                        model_name = model_names[choice_num - 1]
                        self.handle_model_selection(model_name)
                    else:
                        print("❌ Invalid choice. Please select a valid number.")
                        
                except ValueError:
                    print("❌ Please enter a valid number or command.")
    
    def show_huggingface_status(self):
        """Show Hugging Face connection status"""
        print("\n🔗 Hugging Face Status:")
        print("=" * 40)
        
        hf_status = self.config.get_deepseek_models_status()
        
        if hf_status.get("huggingface_available", False):
            print("✅ Hugging Face Hub: Available")
            if "deepseek_models_found" in hf_status:
                print(f"📦 DeepSeek Models: {hf_status['deepseek_models_found']}+ found")
            print(f"🔧 Status: {hf_status.get('status', 'Connected')}")
        else:
            print("❌ Hugging Face Hub: Not available")
            print("💡 Install: pip install huggingface-hub")
        
        input("\nPress Enter to continue...")
  
def main():
    try:
        download_manager = SmartDownloadManager()
        download_manager.main_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Download manager closed by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("💡 Please check your installation and try again.")

if __name__ == "__main__":
    main()

