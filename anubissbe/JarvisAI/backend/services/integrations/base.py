from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseIntegration(ABC):
    @abstractmethod
    async def execute(self, action: str, parameters: Dict[str, Any], api_key: Optional[str] = None) -> Any:
        """Execute an action with the given parameters"""
        pass