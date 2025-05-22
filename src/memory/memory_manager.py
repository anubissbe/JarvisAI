"""
Memory manager for Jarvis AI Assistant.
Handles conversation history, user preferences, and long-term knowledge storage.
"""

import logging
import json
import os
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

class MemoryManager:
    """Manages memory for the Jarvis AI Assistant.
    
    This class handles:
    1. Short-term conversation context
    2. Long-term conversation history
    3. User-provided knowledge
    4. User preferences
    """
    
    def __init__(self, memory_dir: Optional[str] = None, max_context_size: int = 10):
        """Initialize the memory manager.
        
        Args:
            memory_dir: Optional directory path for storing memory files.
            max_context_size: Maximum number of interactions to keep in short-term memory.
        """
        self.logger = logging.getLogger("jarvis.memory")
        
        # Set up memory storage directory
        self.memory_dir = memory_dir or os.path.expanduser("~/.jarvis/memory")
        os.makedirs(self.memory_dir, exist_ok=True)
        
        # Conversation context for the current session
        self.current_context = []
        
        # Maximum context size (number of interactions to keep in short-term memory)
        self.max_context_size = max_context_size
        
        # Load user knowledge and preferences
        self.user_knowledge = self._load_json_file("user_knowledge.json", default=[])
        self.user_preferences = self._load_json_file("user_preferences.json", default={})
        
        self.logger.info("Memory manager initialized.")
    
    def _load_json_file(self, filename: str, default: Any = None) -> Any:
        """Load data from a JSON file.
        
        Args:
            filename: The name of the file to load.
            default: The default value to return if the file doesn't exist.
            
        Returns:
            The loaded data or the default value.
        """
        filepath = os.path.join(self.memory_dir, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading {filename}: {e}")
                return default
        return default
    
    def _save_json_file(self, filename: str, data: Any) -> bool:
        """Save data to a JSON file.
        
        Args:
            filename: The name of the file to save.
            data: The data to save.
            
        Returns:
            True if successful, False otherwise.
        """
        filepath = os.path.join(self.memory_dir, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Error saving {filename}: {e}")
            return False
    
    def add_interaction(self, user_input: str, response: str, 
                        intent: Optional[str] = None, 
                        entities: Optional[Dict[str, Any]] = None,
                        knowledge_info: Optional[Dict[str, Any]] = None) -> None:
        """Add a user interaction to memory.
        
        Args:
            user_input: The user's input text.
            response: Jarvis's response text.
            intent: The identified intent.
            entities: Any extracted entities.
            knowledge_info: Any knowledge information used for the response.
        """
        # Create interaction record
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "response": response,
            "intent": intent,
            "entities": entities or {}
        }
        
        # Add knowledge info if available
        if knowledge_info:
            # Store only essential knowledge info to save space
            interaction["knowledge_info"] = {
                "sources": knowledge_info.get("sources", []),
                "from_web": knowledge_info.get("from_web", False),
                "from_vector_db": knowledge_info.get("from_vector_db", False),
                "timestamp": knowledge_info.get("timestamp", "")
            }
        
        # Add to current context
        self.current_context.append(interaction)
        
        # Trim context if it exceeds maximum size
        if len(self.current_context) > self.max_context_size:
            self.current_context = self.current_context[-self.max_context_size:]
        
        # Add to conversation history file
        self._append_to_history(interaction)
    
    def _append_to_history(self, interaction: Dict[str, Any]) -> None:
        """Append an interaction to the conversation history file.
        
        Args:
            interaction: The interaction record to append.
        """
        # Create a date-based filename for better organization
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"history_{today}.jsonl"
        filepath = os.path.join(self.memory_dir, filename)
        
        try:
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(json.dumps(interaction, ensure_ascii=False) + '\n')
        except Exception as e:
            self.logger.error(f"Error appending to history: {e}")
    
    def get_conversation_context(self) -> List[Dict[str, Any]]:
        """Get the current conversation context.
        
        Returns:
            A list of interaction records from the current conversation.
        """
        return self.current_context
    
    def clear_conversation_context(self) -> None:
        """Clear the current conversation context."""
        self.current_context = []
        self.logger.info("Conversation context cleared.")
    
    def add_user_knowledge(self, information: str) -> bool:
        """Add user-provided knowledge to long-term memory.
        
        Args:
            information: The information provided by the user.
            
        Returns:
            True if successful, False otherwise.
        """
        knowledge_item = {
            "timestamp": datetime.now().isoformat(),
            "content": information
        }
        
        self.user_knowledge.append(knowledge_item)
        return self._save_json_file("user_knowledge.json", self.user_knowledge)
    
    def get_user_knowledge(self) -> List[Dict[str, Any]]:
        """Get all user-provided knowledge.
        
        Returns:
            A list of knowledge items.
        """
        return self.user_knowledge
    
    def search_user_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """Search user knowledge for relevant information.
        
        Args:
            query: The search query.
            
        Returns:
            A list of matching knowledge items.
        """
        # Simple search implementation
        # In a real system, use more sophisticated information retrieval
        query_lower = query.lower()
        return [item for item in self.user_knowledge if query_lower in item["content"].lower()]
    
    def set_user_preference(self, key: str, value: Any) -> bool:
        """Set a user preference.
        
        Args:
            key: The preference key.
            value: The preference value.
            
        Returns:
            True if successful, False otherwise.
        """
        self.user_preferences[key] = value
        return self._save_json_file("user_preferences.json", self.user_preferences)
    
    def get_user_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference.
        
        Args:
            key: The preference key.
            default: The default value if the preference doesn't exist.
            
        Returns:
            The preference value or the default.
        """
        return self.user_preferences.get(key, default)
    
    def get_recent_conversations(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get recent conversation history.
        
        Args:
            days: Number of days to look back.
            
        Returns:
            A list of recent interactions.
        """
        # Get list of history files from the past n days
        recent_files = []
        for i in range(days):
            date = (datetime.now() - i).strftime("%Y-%m-%d")
            filename = f"history_{date}.jsonl"
            filepath = os.path.join(self.memory_dir, filename)
            if os.path.exists(filepath):
                recent_files.append(filepath)
        
        # Load and combine records
        recent_interactions = []
        for filepath in recent_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            recent_interactions.append(json.loads(line))
            except Exception as e:
                self.logger.error(f"Error reading history file {filepath}: {e}")
        
        # Sort by timestamp
        recent_interactions.sort(key=lambda x: x.get("timestamp", ""))
        
        return recent_interactions