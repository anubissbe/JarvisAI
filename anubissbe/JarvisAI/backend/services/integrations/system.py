import os
import platform
import psutil
import logging
from typing import Dict, Any, Optional

from .base import BaseIntegration

logger = logging.getLogger(__name__)

class SystemIntegration(BaseIntegration):
    async def execute(self, action: str, parameters: Dict[str, Any], api_key: Optional[str] = None) -> Any:
        """Execute a system action"""
        action = action.lower()
        
        if action == "get_system_info":
            return self._get_system_info()
        elif action == "get_memory_usage":
            return self._get_memory_usage()
        elif action == "get_disk_usage":
            return self._get_disk_usage()
        elif action == "get_cpu_usage":
            return self._get_cpu_usage()
        else:
            raise ValueError(f"Unknown system action: {action}")
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return {
            "system": platform.system(),
            "node": platform.node(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor()
        }
    
    def _get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage information"""
        memory = psutil.virtual_memory()
        return {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used,
            "free": memory.free
        }
    
    def _get_disk_usage(self) -> Dict[str, Any]:
        """Get disk usage information"""
        disk = psutil.disk_usage('/')
        return {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent
        }
    
    def _get_cpu_usage(self) -> Dict[str, Any]:
        """Get CPU usage information"""
        return {
            "percent": psutil.cpu_percent(interval=1),
            "count": psutil.cpu_count()
        }