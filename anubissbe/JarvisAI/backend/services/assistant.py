from typing import Dict, Any, List, Optional
import logging
from models.assistant import AssistantResponse, Command
from models.user import User
from .ai import AIService
from .integrations import IntegrationManager

logger = logging.getLogger(__name__)

class AssistantService:
    def __init__(self):
        self.ai_service = AIService()
        self.integration_manager = IntegrationManager()
    
    async def process_query(self, query: str, context: Optional[Dict[str, Any]], user: User) -> AssistantResponse:
        """Process a user query and generate a response"""
        try:
            # Get user settings for AI model configuration
            user_settings = await self._get_user_settings(user.id)
            
            # Process the query with AI
            ai_response = await self.ai_service.generate_response(
                query, 
                context, 
                user_settings.ai_model
            )
            
            # Extract any commands from the AI response
            commands = self._extract_commands(ai_response)
            
            # Format the final response
            response = AssistantResponse(
                text=ai_response.get("text", ""),
                commands=commands,
                data=ai_response.get("data")
            )
            
            return response
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise
    
    async def execute_command(self, command: Command, user: User) -> Any:
        """Execute a specific command using the appropriate integration"""
        try:
            # Get user settings for integration configuration
            user_settings = await self._get_user_settings(user.id)
            
            # Execute the command using the integration manager
            result = await self.integration_manager.execute_command(
                command,
                user_settings.integrations
            )
            
            return result
        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            raise
    
    async def _get_user_settings(self, user_id: str):
        """Get user settings from the database"""
        from .settings import SettingsService
        settings_service = SettingsService()
        return await settings_service.get_settings(user_id)
    
    def _extract_commands(self, ai_response: Dict[str, Any]) -> List[Command]:
        """Extract commands from AI response"""
        commands = []
        if "commands" in ai_response and isinstance(ai_response["commands"], list):
            for cmd_data in ai_response["commands"]:
                try:
                    command = Command(**cmd_data)
                    commands.append(command)
                except Exception as e:
                    logger.warning(f"Invalid command format: {str(e)}")
        
        return commands