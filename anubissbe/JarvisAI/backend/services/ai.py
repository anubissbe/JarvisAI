import os
import logging
from typing import Dict, Any, Optional
import openai
from models.settings import AIModelSettings

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        # Initialize OpenAI API key from environment variable
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            logger.warning("OpenAI API key not found in environment variables")
    
    async def generate_response(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]], 
        model_settings: AIModelSettings
    ) -> Dict[str, Any]:
        """Generate a response using the AI model"""
        try:
            # Prepare the messages for the AI
            messages = self._prepare_messages(query, context)
            
            # Call the OpenAI API
            response = await openai.ChatCompletion.acreate(
                model=model_settings.model,
                messages=messages,
                temperature=model_settings.temperature,
                max_tokens=model_settings.max_tokens,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            # Process and parse the response
            return self._process_response(response)
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            return {"text": f"I'm sorry, I encountered an error: {str(e)}"}
    
    def _prepare_messages(self, query: str, context: Optional[Dict[str, Any]]) -> list:
        """Prepare the messages for the AI model"""
        messages = [
            {"role": "system", "content": "You are Jarvis, an advanced AI assistant. You can help with various tasks and provide information."}
        ]
        
        # Add context if provided
        if context and "history" in context and isinstance(context["history"], list):
            for msg in context["history"]:
                if "role" in msg and "content" in msg:
                    messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add the current query
        messages.append({"role": "user", "content": query})
        
        return messages
    
    def _process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Process and parse the AI response"""
        if not response or "choices" not in response or not response["choices"]:
            return {"text": "I'm sorry, I couldn't generate a response."}
        
        content = response["choices"][0]["message"]["content"]
        
        # Try to extract structured data if available
        result = {"text": content}
        
        try:
            # Check if the response contains command markers
            if "[[COMMAND:" in content and "]]" in content:
                commands = []
                text_parts = []
                current_pos = 0
                
                while "[[COMMAND:" in content[current_pos:]:
                    cmd_start = content.find("[[COMMAND:", current_pos)
                    if cmd_start > current_pos:
                        text_parts.append(content[current_pos:cmd_start])
                    
                    cmd_end = content.find("]]", cmd_start)
                    if cmd_end == -1:
                        break
                    
                    cmd_str = content[cmd_start + 10:cmd_end]
                    try:
                        import json
                        cmd_data = json.loads(cmd_str)
                        commands.append(cmd_data)
                    except:
                        pass
                    
                    current_pos = cmd_end + 2
                
                if current_pos < len(content):
                    text_parts.append(content[current_pos:])
                
                result["text"] = "".join(text_parts)
                result["commands"] = commands
        except Exception as e:
            logger.warning(f"Error parsing AI response: {str(e)}")
        
        return result