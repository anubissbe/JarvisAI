import os
import uuid
from typing import Optional, Dict, Any
import aiohttp
from datetime import datetime

class JarvisAI:
    def __init__(self, knowledge_manager, memory_manager, language_detector):
        self.knowledge_manager = knowledge_manager
        self.memory_manager = memory_manager
        self.language_detector = language_detector
        self.ollama_api_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
        
        # Load system prompt
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        """Load the system prompt from the README file"""
        # The system prompt is stored in the README.md file between triple backticks
        # You would need to implement proper extraction logic here
        return """You are Jarvis, an advanced bilingual AI assistant..."""  # Shortened for brevity

    async def process_message(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process an incoming message and generate a response"""
        
        # Create new conversation ID if none provided
        if not conversation_id:
            conversation_id = str(uuid.uuid4())

        # Detect language
        language = self.language_detector.detect(message)

        # Get relevant context from memory and knowledge base
        memory_context = await self.memory_manager.get_context(conversation_id)
        knowledge_context = await self.knowledge_manager.search_relevant_info(message)

        # Combine all context
        full_context = {
            "memory": memory_context,
            "knowledge": knowledge_context,
            **(context or {})
        }

        # Prepare the prompt
        prompt = self._prepare_prompt(message, full_context, language)

        # Get response from Ollama
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.ollama_api_url}/api/chat",
                json={
                    "model": "jarvis",
                    "messages": [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "stream": False
                }
            ) as response:
                result = await response.json()

        # Extract the response
        ai_response = result["message"]["content"]

        # Store interaction in memory
        await self.memory_manager.store_interaction(
            conversation_id=conversation_id,
            user_message=message,
            ai_response=ai_response,
            context=full_context,
            timestamp=datetime.utcnow()
        )

        return {
            "response": ai_response,
            "language": language,
            "sources": knowledge_context.get("sources", []),
            "conversation_id": conversation_id
        }

    def _prepare_prompt(self, message: str, context: Dict[str, Any], language: str) -> str:
        """Prepare the prompt with context for the AI"""
        prompt_parts = []

        # Add memory context if available
        if context.get("memory"):
            prompt_parts.append("Previous conversation context:")
            prompt_parts.append(context["memory"])

        # Add knowledge context if available
        if context.get("knowledge"):
            prompt_parts.append("Relevant knowledge:")
            prompt_parts.append(context["knowledge"])

        # Add the user's message
        prompt_parts.append(f"User message ({language}):")
        prompt_parts.append(message)

        # Add any additional context
        for key, value in context.items():
            if key not in ["memory", "knowledge"]:
                prompt_parts.append(f"{key}:")
                prompt_parts.append(str(value))

        # Combine all parts with clear separation
        return "\n\n".join(prompt_parts)