"""
Main engine for Jarvis AI Assistant.
This module implements the core functionality of the Jarvis system.
"""

import logging
import importlib
import sys
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

# Use absolute imports for better reliability
try:
    from src.language.processor import LanguageProcessor
    from src.memory.memory_manager import MemoryManager
    from src.knowledge.knowledge_base import KnowledgeBase
    from src.llm.ollama_client import OllamaClient
except ImportError:
    # Fallback to relative imports if the module is not in the path
    from ..language.processor import LanguageProcessor
    from ..memory.memory_manager import MemoryManager
    from ..knowledge.knowledge_base import KnowledgeBase
    from ..llm.ollama_client import OllamaClient

class JarvisEngine:
    """Core engine for Jarvis AI Assistant.
    
    This class coordinates all components of the Jarvis system,
    including language processing, memory management, and knowledge retrieval.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Jarvis Engine.
        
        Args:
            config: Optional configuration dictionary for Jarvis.
        """
        self.logger = logging.getLogger("jarvis.engine")
        self.config = config or {}
        
        self.logger.info("Initializing Jarvis AI Assistant...")
        
        # Set up configuration values
        memory_dir = self.config.get("memory_dir")
        knowledge_dir = self.config.get("knowledge_dir")
        ollama_url = self.config.get("ollama_url", "http://localhost:11434")
        max_context_size = self.config.get("max_context_size", 10)
        
        # Initialize core components
        self.language = LanguageProcessor()
        self.memory = MemoryManager(memory_dir=memory_dir, max_context_size=max_context_size)
        self.knowledge = KnowledgeBase(knowledge_dir=knowledge_dir, config=self.config)
        
        # Initialize LLM client
        try:
            self.logger.info(f"Connecting to Ollama LLM at {ollama_url}")
            self.llm = OllamaClient(base_url=ollama_url, model="jarvis")
            self.logger.info("Successfully connected to Ollama LLM")
        except Exception as e:
            self.logger.error(f"Failed to initialize Ollama client: {e}")
            self.logger.warning("LLM functionality will be limited")
            self.llm = None
        
        self.logger.info("Jarvis initialization complete.")
        
        # Persona configuration
        self.persona = {
            "en": {
                "name": "Jarvis",
                "greeting": "Hello, I'm Jarvis, your advanced AI assistant. How may I help you today?",
                "farewell": "Goodbye. I'll be here when you need me.",
                "thinking": "Let me think about that...",
                "confused": "I'm sorry, I didn't quite understand that. Could you rephrase your question?",
                "acknowledgment": "I understand. Let me handle that for you."
            },
            "nl": {
                "name": "Jarvis",
                "greeting": "Hallo, ik ben Jarvis, uw geavanceerde AI-assistent. Hoe kan ik u vandaag helpen?",
                "farewell": "Tot ziens. Ik ben er wanneer u me nodig heeft.",
                "thinking": "Laat me daar even over nadenken...",
                "confused": "Het spijt me, ik begrijp het niet helemaal. Kunt u uw vraag anders formuleren?",
                "acknowledgment": "Ik begrijp het. Laat mij dat voor u regelen."
            }
        }
    
    def process_input(self, user_input: str, force_web_search: bool = False) -> str:
        """Process user input and generate a response.
        
        Args:
            user_input: The text input from the user.
            force_web_search: Whether to force a web search for this query.
            
        Returns:
            A string response from Jarvis.
        """
        # Detect language
        language = self.language.detect_language(user_input)
        self.logger.debug(f"Detected language: {language}")
        
        # Process the input in the context of conversation history
        context = self.memory.get_conversation_context()
        
        # Extract intent and entities
        intent, entities = self.language.extract_intent_and_entities(user_input, language)
        self.logger.debug(f"Intent: {intent}, Entities: {entities}")
        
        # Check if this is a command to search the web
        if self._is_web_search_command(user_input, intent, entities, language):
            force_web_search = True
            # Extract the actual query from the web search command
            user_input = self._extract_query_from_web_search_command(user_input, language)
            self.logger.info(f"Web search command detected. Query: {user_input}")
        
        # Handle simple intents directly
        if intent == "greeting":
            response = self.persona[language]["greeting"]
        elif intent == "farewell":
            response = self.persona[language]["farewell"]
        else:
            # For more complex queries, first check the knowledge base
            knowledge_info = self.knowledge.query(intent, entities, language, force_web_search)
            
            # If LLM is available, use it for response generation
            if self.llm:
                # Prepare system message with any retrieved knowledge
                system_message = self._prepare_system_message(intent, entities, knowledge_info, language)
                
                # Format chat history for context
                chat_history = []
                if context:
                    chat_history = self.llm.format_chat_history(context[-5:])  # Use last 5 interactions
                
                # Add the current user message
                chat_history.append({"role": "user", "content": user_input})
                
                # Get response from LLM
                llm_response, metadata = self.llm.chat(chat_history, system_message)
                self.logger.debug(f"LLM response metadata: {metadata}")
                
                # Use the LLM response
                response = llm_response
            else:
                # Fallback to template-based response if LLM is unavailable
                response = self.language.generate_response(intent, entities, knowledge_info, context, language)
        
        # Update memory with this interaction, including knowledge info
        self.memory.add_interaction(user_input, response, intent, entities, knowledge_info)
        
        return response
    
    def _is_web_search_command(self, text: str, intent: str, entities: Dict[str, Any], language: str) -> bool:
        """Check if the input is a command to search the web.
        
        Args:
            text: The user input text.
            intent: The identified intent.
            entities: The extracted entities.
            language: The detected language code.
            
        Returns:
            True if this is a web search command, False otherwise.
        """
        text_lower = text.lower()
        
        # English web search commands
        if language == "en":
            search_prefixes = [
                "search for", "search the web for", "look up", "google", "find information about",
                "search", "web search", "find", "search online for"
            ]
            
            for prefix in search_prefixes:
                if text_lower.startswith(prefix):
                    return True
        
        # Dutch web search commands
        else:  # language == "nl"
            search_prefixes = [
                "zoek naar", "zoek op het web naar", "opzoeken", "google", "zoek informatie over",
                "zoek", "webzoekopdracht", "vind", "zoek online naar"
            ]
            
            for prefix in search_prefixes:
                if text_lower.startswith(prefix):
                    return True
        
        return False
    
    def _extract_query_from_web_search_command(self, text: str, language: str) -> str:
        """Extract the actual query from a web search command.
        
        Args:
            text: The user input text.
            language: The detected language code.
            
        Returns:
            The extracted query.
        """
        text_lower = text.lower()
        
        # English web search commands
        if language == "en":
            search_prefixes = [
                "search for", "search the web for", "look up", "google", "find information about",
                "search", "web search", "find", "search online for"
            ]
        # Dutch web search commands
        else:  # language == "nl"
            search_prefixes = [
                "zoek naar", "zoek op het web naar", "opzoeken", "google", "zoek informatie over",
                "zoek", "webzoekopdracht", "vind", "zoek online naar"
            ]
        
        # Find the matching prefix
        matching_prefix = None
        for prefix in search_prefixes:
            if text_lower.startswith(prefix):
                matching_prefix = prefix
                break
        
        if matching_prefix:
            # Remove the prefix to get the query
            query = text[len(matching_prefix):].strip()
            
            # Remove leading ":" or "?" if present
            if query.startswith(":") or query.startswith("?"):
                query = query[1:].strip()
                
            return query
        
        # If no prefix matched, return the original text
        return text
        
    def add_to_knowledge_base(self, content: str, metadata: Dict[str, Any] = None) -> bool:
        """Add information to the knowledge base.
        
        Args:
            content: The content to add to the knowledge base.
            metadata: Additional metadata for the content.
            
        Returns:
            True if successful, False otherwise.
        """
        if not metadata:
            metadata = {}
        
        # Ensure language is specified in metadata
        if "language" not in metadata:
            # Detect language
            language = self.language.detect_language(content)
            metadata["language"] = language
        
        # Ensure timestamp is present
        if "timestamp" not in metadata:
            from datetime import datetime
            metadata["timestamp"] = datetime.now().isoformat()
        
        # Add source if not present
        if "source" not in metadata:
            metadata["source"] = "User Input"
        
        # Add to vector database if available
        if self.knowledge.collection:
            return self.knowledge.add_to_vector_db(content, metadata)
        
        return False
    
    def direct_web_search(self, query: str, language: str = None) -> List[Dict[str, Any]]:
        """Perform a direct web search without going through the knowledge base.
        
        Args:
            query: The search query.
            language: Optional language code (detected if not provided).
            
        Returns:
            A list of search results.
        """
        if not language:
            language = self.language.detect_language(query)
        
        if hasattr(self.knowledge, "web_search"):
            return self.knowledge.web_search.search(query, language)
        
        return []
    
    def get_conversation_summary(self, max_interactions: int = 10) -> str:
        """Get a summary of recent conversations.
        
        Args:
            max_interactions: Maximum number of interactions to include.
            
        Returns:
            A formatted string with the conversation summary.
        """
        context = self.memory.get_conversation_context()
        
        if not context:
            return "No conversation history available."
        
        # Take the most recent interactions
        recent = context[-min(max_interactions, len(context)):]
        
        # Format the summary
        summary = "Recent conversation history:\n\n"
        
        for i, interaction in enumerate(recent):
            timestamp = interaction.get("timestamp", "")
            
            # Try to format the timestamp if it's an ISO format string
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(timestamp)
                timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                pass
            
            user_input = interaction.get("user_input", "")
            response = interaction.get("response", "")
            
            summary += f"[{timestamp}]\n"
            summary += f"User: {user_input}\n"
            summary += f"Jarvis: {response}\n\n"
        
        return summary
        
    def _prepare_system_message(self, intent: str, entities: Dict[str, Any], 
                               knowledge_info: Optional[Dict[str, Any]], 
                               language: str) -> str:
        """Prepare a system message for the LLM with context and knowledge.
        
        Args:
            intent: The identified intent.
            entities: The extracted entities.
            knowledge_info: Knowledge retrieved for this query.
            language: The detected language code.
            
        Returns:
            A system message string for the LLM.
        """
        # Start with the base persona information
        if language == "en":
            system_message = "You are Jarvis, an advanced AI assistant. "
            system_message += "Respond in English with a helpful, friendly, and slightly witty tone. "
            system_message += "Be concise but thorough. "
        else:  # Dutch
            system_message = "Je bent Jarvis, een geavanceerde AI-assistent. "
            system_message += "Reageer in het Nederlands met een behulpzame, vriendelijke en licht geestige toon. "
            system_message += "Wees beknopt maar grondig. "
        
        # Add knowledge information if available
        if knowledge_info:
            # Different handling based on the source of information
            from_web = knowledge_info.get("from_web", False)
            from_vector_db = knowledge_info.get("from_vector_db", False)
            
            if from_web:
                if language == "en":
                    system_message += "\n\nI've searched the web and found this information: "
                else:  # Dutch
                    system_message += "\n\nIk heb het web doorzocht en deze informatie gevonden: "
            elif from_vector_db:
                if language == "en":
                    system_message += "\n\nFrom my knowledge base, I have this information: "
                else:  # Dutch
                    system_message += "\n\nUit mijn kennisbank heb ik deze informatie: "
            else:
                if language == "en":
                    system_message += "\n\nYou have the following relevant information: "
                else:  # Dutch
                    system_message += "\n\nJe hebt de volgende relevante informatie: "
            
            # Add the content
            system_message += knowledge_info.get("content", "")
            
            # Add timestamp if available
            if knowledge_info.get("timestamp"):
                try:
                    timestamp = datetime.fromisoformat(knowledge_info["timestamp"])
                    date_str = timestamp.strftime("%Y-%m-%d")
                    if language == "en":
                        system_message += f"\nThis information was last updated on {date_str}."
                    else:  # Dutch
                        system_message += f"\nDeze informatie is voor het laatst bijgewerkt op {date_str}."
                except Exception:
                    pass
            
            # Add sources
            if knowledge_info.get("sources"):
                if language == "en":
                    system_message += f"\nSources: {', '.join(knowledge_info['sources'])}"
                    system_message += "\nPlease cite these sources in your response when appropriate."
                else:  # Dutch
                    system_message += f"\nBronnen: {', '.join(knowledge_info['sources'])}"
                    system_message += "\nVermeld deze bronnen in je antwoord waar nodig."
        
        # Add instructions for response formatting
        if language == "en":
            system_message += "\n\nFormat your response in a clear, structured way. Use markdown for headers and lists when appropriate."
            system_message += "\nIf you're not sure about the answer, acknowledge the limitations of your information."
        else:  # Dutch
            system_message += "\n\nFormatteer je antwoord op een duidelijke, gestructureerde manier. Gebruik markdown voor koppen en lijsten indien nodig."
            system_message += "\nAls je niet zeker bent van het antwoord, erken dan de beperkingen van je informatie."
        
        return system_message
        
    def verify_information(self, query: str, language: str) -> Tuple[str, List[str]]:
        """Verify information using internet sources.
        
        Args:
            query: The information to verify.
            language: The language code (en/nl).
            
        Returns:
            A tuple containing the verified information and source citations.
        """
        return self.knowledge.verify_information(query, language)
    
    def add_user_knowledge(self, information: str) -> bool:
        """Add user-provided knowledge to the system.
        
        Args:
            information: The information provided by the user.
            
        Returns:
            True if successful, False otherwise.
        """
        return self.memory.add_user_knowledge(information)
    
    def get_response_with_persona(self, content: str, language: str) -> str:
        """Apply the Jarvis persona to the response content.
        
        This ensures responses maintain the Jarvis personality traits
        (helpful, friendly, slightly witty).
        
        Args:
            content: The raw response content.
            language: The language code (en/nl).
            
        Returns:
            Response with appropriate persona elements applied.
        """
        return self.language.apply_persona(content, language)