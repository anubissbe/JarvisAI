"""
Main engine for Jarvis AI Assistant.
This module implements the core functionality of the Jarvis system.
"""

import logging
import importlib
import sys
import time
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
        
        # Add metrics tracking
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.last_error = None
        
        # Component status tracking
        self._components = {
            "language": False,
            "memory": False,
            "knowledge": False,
            "llm": False
        }
        
        self.logger.info("Initializing Jarvis AI Assistant...")
        
        try:
            # Set up configuration values with validation
            memory_dir = self._validate_dir_path(self.config.get("memory_dir"))
            knowledge_dir = self._validate_dir_path(self.config.get("knowledge_dir"))
            ollama_url = self._validate_url(self.config.get("ollama_url", "http://localhost:11434"))
            max_context_size = min(max(1, self.config.get("max_context_size", 10)), 100)
            
            # Initialize core components with cleanup on failure
            try:
                self.language = LanguageProcessor()
                self._components["language"] = True
                
                self.memory = MemoryManager(memory_dir=memory_dir, max_context_size=max_context_size)
                self._components["memory"] = True
                
                self.knowledge = KnowledgeBase(knowledge_dir=knowledge_dir, config=self.config)
                self._components["knowledge"] = True
                
            except Exception as e:
                self.logger.error(f"Failed to initialize core components: {e}")
                self._cleanup_failed_init()
                raise
            
            # Initialize LLM client with timeout and retry
            self.llm = None
            for attempt in range(3):  # Try 3 times
                try:
                    self.logger.info(f"Connecting to Ollama LLM at {ollama_url} (attempt {attempt + 1})")
                    self.llm = OllamaClient(
                        base_url=ollama_url,
                        model="jarvis",
                        timeout=10.0  # 10 second timeout
                    )
                    # Test the connection
                    self.llm.get_available_models()
                    self._components["llm"] = True
                    self.logger.info("Successfully connected to Ollama LLM")
                    break
                    
                except Exception as e:
                    self.logger.warning(f"LLM connection attempt {attempt + 1} failed: {e}")
                    if attempt == 2:  # Last attempt
                        self.logger.error("Failed to initialize Ollama client after 3 attempts")
                        self.logger.warning("LLM functionality will be limited")
            
            self.logger.info("Jarvis initialization complete.")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Jarvis: {e}")
            self._cleanup_failed_init()
            raise
        
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
        # Increment request counter
        self.request_count += 1
        request_id = f"req_{int(time.time())}_{self.request_count}"
        
        # Record start time for performance tracking
        start_time = time.time()
        language = "en"  # Default language in case of early error
        
        try:
            # Input validation
            if not user_input or not user_input.strip():
                raise ValueError("Empty input")
            
            user_input = user_input.strip()
            if len(user_input) > 1000:  # Reasonable limit for input length
                raise ValueError("Input too long (max 1000 characters)")
            
            # Detect language
            language = self.language.detect_language(user_input)
            self.logger.debug(f"[{request_id}] Detected language: {language}")
            
            # Get conversation context with automatic pruning of old entries
            context = self.memory.get_conversation_context()
            if len(context) > self.memory.max_context_size:
                self.logger.debug(f"[{request_id}] Pruning conversation context")
                context = context[-self.memory.max_context_size:]
            
            # Extract intent and entities
            intent, entities = self.language.extract_intent_and_entities(user_input, language)
            self.logger.debug(f"[{request_id}] Intent: {intent}, Entities: {entities}")
            
            # Check if this is a command to search the web
            if self._is_web_search_command(user_input, intent, entities, language):
                force_web_search = True
                user_input = self._extract_query_from_web_search_command(user_input, language)
                self.logger.info(f"[{request_id}] Web search command detected. Query: {user_input}")
            
            # Handle simple intents directly
            if intent == "greeting":
                response = self.persona[language]["greeting"]
            elif intent == "farewell":
                response = self.persona[language]["farewell"]
            else:
                # For more complex queries, first check the knowledge base
                try:
                    knowledge_info = self.knowledge.query(
                        intent, entities, language, force_web_search,
                        timeout=5.0  # 5 second timeout for knowledge queries
                    )
                except TimeoutError:
                    self.logger.warning(f"[{request_id}] Knowledge base query timed out")
                    knowledge_info = None
                
                # Try LLM first, fall back to templates if needed
                response = None
                llm_error = None
                
                if self.llm:
                    try:
                        # Prepare system message
                        system_message = self._prepare_system_message(
                            intent, entities, knowledge_info, language
                        )
                        
                        # Format chat history
                        chat_history = []
                        if context:
                            chat_history = self.llm.format_chat_history(
                                context[-min(5, len(context)):]  # Use last 5 interactions max
                            )
                        
                        # Add current message
                        chat_history.append({"role": "user", "content": user_input})
                        
                        # Get LLM response with timeout
                        llm_response, metadata = await asyncio.wait_for(
                            self.llm.chat(chat_history, system_message),
                            timeout=10.0  # 10 second timeout
                        )
                        
                        self.logger.debug(f"[{request_id}] LLM response metadata: {metadata}")
                        response = llm_response
                        
                    except Exception as e:
                        llm_error = str(e)
                        self.logger.error(f"[{request_id}] LLM error: {e}")
                
                # Fall back to template response if LLM failed or is unavailable
                if not response:
                    self.logger.info(f"[{request_id}] Using template fallback response")
                    response = self.language.generate_response(
                        intent, entities, knowledge_info, context, language
                    )
                    if llm_error:
                        # Add a note about the fallback if in debug mode
                        if self.config.get("debug", False):
                            response += f"\n\n[Debug: Using template fallback due to LLM error: {llm_error}]"
            
            # Update memory with bounded size
            try:
                self.memory.add_interaction(
                    user_input, response, intent, entities, knowledge_info,
                    metadata={"request_id": request_id}
                )
            except Exception as e:
                self.logger.error(f"[{request_id}] Failed to update memory: {e}")
            
            # Log performance metrics
            process_time = time.time() - start_time
            self.logger.info(
                f"[{request_id}] Processed input in {process_time:.2f}s "
                f"(language: {language}, intent: {intent})"
            )
            
            return response
            
        except ValueError as e:
            # Handle validation errors
            self.error_count += 1
            self.last_error = str(e)
            self.logger.warning(f"[{request_id}] Validation error: {e}")
            
            return (
                "Sorry, uw invoer is niet geldig. Probeer het opnieuw." if language == "nl"
                else "Sorry, your input is not valid. Please try again."
            )
            
        except Exception as e:
            # Handle other errors
            self.error_count += 1
            self.last_error = str(e)
            self.logger.error(f"[{request_id}] Error processing input: {e}", exc_info=True)
            
            # Return a friendly error message
            return (
                "Sorry, er is een fout opgetreden bij het verwerken van uw verzoek. "
                "Probeer het later nog eens." if language == "nl"
                else "Sorry, an error occurred while processing your request. Please try again later."
            )
        
        finally:
            # Clean up any resources if needed
            self._cleanup_request_resources(request_id)
    
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
        
    def _validate_dir_path(self, path: Optional[str]) -> Optional[str]:
        """Validate and create directory path if needed."""
        if not path:
            return None
            
        try:
            path = os.path.expanduser(path)
            os.makedirs(path, exist_ok=True)
            return path
        except Exception as e:
            self.logger.error(f"Invalid directory path {path}: {e}")
            raise ValueError(f"Invalid directory path: {e}")
    
    def _validate_url(self, url: str) -> str:
        """Validate URL format."""
        if not url.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return url
    
    def _cleanup_failed_init(self) -> None:
        """Clean up resources after failed initialization."""
        for component, initialized in self._components.items():
            if initialized:
                try:
                    if hasattr(self, component):
                        obj = getattr(self, component)
                        if hasattr(obj, "cleanup"):
                            obj.cleanup()
                except Exception as e:
                    self.logger.error(f"Error cleaning up {component}: {e}")
    
    def _cleanup_request_resources(self, request_id: str) -> None:
        """Clean up any resources allocated for a specific request."""
        try:
            # Add any request-specific cleanup here
            pass
        except Exception as e:
            self.logger.error(f"Error in request cleanup for {request_id}: {e}")
    
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