import os
import logging
from typing import Dict, Any, Optional
import requests
from models.settings import AIModelSettings

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
    
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
            
            # Call the Ollama API
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": model_settings.model,
                    "messages": messages,
                    "options": {
                        "temperature": model_settings.temperature,
                        "num_predict": model_settings.max_tokens
                    }
                }
            )
            response.raise_for_status()
            
            # Process and parse the response
            return self._process_response(response.json())
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            return {"text": f"I'm sorry, I encountered an error: {str(e)}"}
    
    def _prepare_messages(self, query: str, context: Optional[Dict[str, Any]]) -> list:
        """Prepare the messages for the AI model"""
        system_message = "You are Jarvis, an advanced AI assistant. You can help with various tasks and provide information."
        
        # Add document context if available
        if context and "documents" in context and context["documents"]:
            document_context = "I have access to the following information from your documents:\n\n"
            for i, doc in enumerate(context["documents"]):
                document_context += f"Document {i+1}: {doc['title']}\n"
                document_context += f"Content: {doc['content']}\n\n"
            
            system_message += f"\n\n{document_context}"
            system_message += "\nWhen answering questions, use this document information when relevant."
        
        messages = [
            {"role": "system", "content": system_message}
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
        if not response or "message" not in response:
            return {"text": "I'm sorry, I couldn't generate a response."}
        
        content = response["message"]["content"]
        
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