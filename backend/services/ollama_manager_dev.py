# Development version of Ollama Manager for single GPU
import httpx
import asyncio
from typing import List, Dict, Optional
import nvidia_ml_py as nvml
import time
import logging

logger = logging.getLogger(__name__)

class OllamaGPUManagerDev:
    """
    Development version for single GPU (RTX 5090 32GB)
    Manages model loading/unloading on a single GPU
    """
    
    def __init__(self, host: str = "http://ollama:11434"):
        self.host = host
        self.client = httpx.AsyncClient(timeout=300.0)
        self.loaded_models = {}  # Track loaded models and their memory usage
        self.gpu_memory_gb = 32  # RTX 5090 32GB
        self.reserved_memory_gb = 2  # Keep 2GB free for operations
        nvml.nvmlInit()
        
        # Model size estimates (in GB)
        self.model_sizes = {
            "llama3.1:8b": 8.5,
            "llama3.1:70b": 40,  # Won't fit, for reference
            "mistral:7b": 7.5,
            "codellama:13b": 13.5,
            "deepseek-r1:14b": 14.5,
            "safespace:7b": 7.5,
            "qwen2.5:14b": 14.5,
            "qwen2.5:7b": 7.5,
            "gemma2:9b": 9.5,
            "phi3:14b": 14.5,
            "yi:34b": 35,  # Won't fit, for reference
        }
        
    async def get_gpu_status(self) -> Dict:
        """Get current GPU memory usage and status"""
        handle = nvml.nvmlDeviceGetHandleByIndex(0)  # Single GPU
        info = nvml.nvmlDeviceGetMemoryInfo(handle)
        
        return {
            "gpu_id": 0,
            "gpu_name": nvml.nvmlDeviceGetName(handle).decode(),
            "total_gb": info.total / (1024**3),
            "used_gb": info.used / (1024**3),
            "free_gb": info.free / (1024**3),
            "utilization": (info.used / info.total) * 100,
            "loaded_models": list(self.loaded_models.keys()),
            "can_load_more": info.free / (1024**3) > self.reserved_memory_gb
        }
    
    async def estimate_loadable_models(self) -> List[str]:
        """Estimate which models can currently be loaded"""
        status = await self.get_gpu_status()
        available_gb = status["free_gb"] - self.reserved_memory_gb
        
        loadable = []
        for model, size in self.model_sizes.items():
            if size <= available_gb and model not in self.loaded_models:
                loadable.append(f"{model} ({size}GB)")
        
        return loadable
    
    async def smart_model_load(self, model_name: str) -> Dict:
        """
        Smart loading with automatic model management
        Will unload least recently used models if needed
        """
        if model_name in self.loaded_models:
            # Update last used time
            self.loaded_models[model_name]["last_used"] = time.time()
            return {"status": "already_loaded", "model": model_name}
        
        model_size = self.model_sizes.get(model_name, 10)  # Default 10GB if unknown
        status = await self.get_gpu_status()
        available_gb = status["free_gb"] - self.reserved_memory_gb
        
        # Check if we need to unload models
        if model_size > available_gb:
            logger.info(f"Need to free {model_size - available_gb:.1f}GB for {model_name}")
            
            # Sort models by last used time (oldest first)
            models_by_age = sorted(
                self.loaded_models.items(),
                key=lambda x: x[1]["last_used"]
            )
            
            freed_gb = 0
            models_to_unload = []
            
            for loaded_model, info in models_by_age:
                if freed_gb >= (model_size - available_gb):
                    break
                models_to_unload.append(loaded_model)
                freed_gb += info["size_gb"]
            
            # Unload models
            for model_to_unload in models_to_unload:
                await self.unload_model(model_to_unload)
                logger.info(f"Unloaded {model_to_unload} to make room")
        
        # Load the requested model
        try:
            response = await self.client.post(
                f"{self.host}/api/pull",
                json={"name": model_name}
            )
            
            # Load into memory
            load_response = await self.client.post(
                f"{self.host}/api/generate",
                json={
                    "model": model_name,
                    "prompt": "",
                    "keep_alive": -1  # Keep in memory
                }
            )
            
            self.loaded_models[model_name] = {
                "size_gb": model_size,
                "loaded_at": time.time(),
                "last_used": time.time()
            }
            
            return {
                "status": "loaded",
                "model": model_name,
                "memory_used_gb": model_size,
                "gpu_status": await self.get_gpu_status()
            }
            
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            return {"status": "error", "error": str(e)}
    
    async def unload_model(self, model_name: str):
        """Unload a specific model from GPU memory"""
        try:
            await self.client.post(
                f"{self.host}/api/generate",
                json={
                    "model": model_name,
                    "keep_alive": 0  # Unload immediately
                }
            )
            
            if model_name in self.loaded_models:
                del self.loaded_models[model_name]
                
            logger.info(f"Unloaded model: {model_name}")
            
        except Exception as e:
            logger.error(f"Failed to unload model {model_name}: {e}")
    
    async def generate_with_auto_load(self, model_name: str, prompt: str, **kwargs):
        """Generate response, automatically loading model if needed"""
        # Ensure model is loaded
        await self.smart_model_load(model_name)
        
        # Generate response
        async with self.client.stream(
            "POST",
            f"{self.host}/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": True,
                **kwargs
            }
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    yield json.loads(line)
        
        # Update last used time
        if model_name in self.loaded_models:
            self.loaded_models[model_name]["last_used"] = time.time()
    
    async def optimize_for_development(self):
        """
        Optimize model loading for development workflow
        Preload commonly used development models
        """
        dev_models = [
            "llama3.1:8b",      # General purpose
            "codellama:13b",    # Code generation
            "mistral:7b"        # Fast inference
        ]
        
        logger.info("Preloading development models...")
        
        for model in dev_models:
            result = await self.smart_model_load(model)
            logger.info(f"Preloaded {model}: {result['status']}")
        
        status = await self.get_gpu_status()
        logger.info(f"GPU Status after preload: {status['used_gb']:.1f}/{status['total_gb']:.1f}GB used")
        
        return status

# Helper class for model recommendations based on task
class ModelSelector:
    """Recommend best model based on task and available GPU memory"""
    
    @staticmethod
    def recommend_model(task_type: str, available_gb: float) -> str:
        recommendations = {
            "general_chat": [
                ("llama3.1:8b", 8.5),
                ("mistral:7b", 7.5),
                ("qwen2.5:7b", 7.5)
            ],
            "code_generation": [
                ("codellama:13b", 13.5),
                ("deepseek-r1:14b", 14.5),
                ("qwen2.5:14b", 14.5)
            ],
            "therapeutic": [
                ("safespace:7b", 7.5),
                ("llama3.1:8b", 8.5)
            ],
            "fast_inference": [
                ("mistral:7b", 7.5),
                ("phi3:14b", 14.5)
            ],
            "multilingual": [
                ("qwen2.5:14b", 14.5),
                ("qwen2.5:7b", 7.5)
            ]
        }
        
        models = recommendations.get(task_type, recommendations["general_chat"])
        
        # Find the best model that fits in available memory
        for model_name, size_gb in models:
            if size_gb <= available_gb:
                return model_name
        
        # If nothing fits, return the smallest model
        return models[-1][0]