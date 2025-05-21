import logging
from typing import Dict, Any
from models.assistant import Command
from models.settings import IntegrationSettings

logger = logging.getLogger(__name__)

class IntegrationManager:
    def __init__(self):
        self.integrations = {}
        self._load_integrations()
    
    def _load_integrations(self):
        """Load available integrations"""
        # Register built-in integrations
        from .integrations.system import SystemIntegration
        from .integrations.web import WebIntegration
        from .integrations.email import EmailIntegration
        from .integrations.weather import WeatherIntegration
        
        self.integrations = {
            "system": SystemIntegration(),
            "web": WebIntegration(),
            "email": EmailIntegration(),
            "weather": WeatherIntegration(),
            # Add more integrations as needed
        }
    
    async def execute_command(self, command: Command, integration_settings: IntegrationSettings) -> Any:
        """Execute a command using the appropriate integration"""
        integration_type = command.type.lower()
        
        if integration_type not in self.integrations:
            raise ValueError(f"Integration '{integration_type}' not found")
        
        # Check if integration is enabled
        if integration_type != "system" and integration_type not in integration_settings.enabled_integrations:
            raise ValueError(f"Integration '{integration_type}' is not enabled")
        
        # Get the integration
        integration = self.integrations[integration_type]
        
        # Get API key if needed
        api_key = None
        if integration_type in integration_settings.api_keys:
            api_key = integration_settings.api_keys[integration_type]
        
        # Execute the command
        return await integration.execute(command.action, command.parameters, api_key)