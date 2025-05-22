#!/usr/bin/env python3
"""
Semantic Memory Store using ChromaDB
This module implements the semantic memory component of Jarvis's Long-Term Memory (LTM) system.
It uses ChromaDB to store and retrieve semantic memories, including:
- Conversation summaries
- Extracted facts and preferences
- Important statements from interactions
"""

import os
import sys
import logging
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('semantic_memory')

class SemanticMemoryStore:
    """Manages semantic memory storage and retrieval using ChromaDB"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8000,
        collection_name: str = "jarvis_implicit_ltm",
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """Initialize the semantic memory store"""
        self.host = host
        self.port = port
        self.collection_name = collection_name
        
        # Configure ChromaDB client
        try:
            self.client = chromadb.HttpClient(
                host=self.host,
                port=self.port,
                settings=Settings(
                    allow_reset=True,  # For development, can be disabled in production
                    anonymized_telemetry=False
                )
            )
            logger.info(f"Connected to ChromaDB at {self.host}:{self.port}")
            
            # Initialize or get the collection
            self.collection = self._initialize_collection(embedding_model)
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {e}")
            raise
    
    def _initialize_collection(self, embedding_model: str) -> chromadb.Collection:
        """Initialize or get the ChromaDB collection"""
        try:
            # Set up the embedding function
            embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=embedding_model
            )
            
            # Get existing collection or create new one
            try:
                collection = self.client.get_collection(
                    name=self.collection_name,
                    embedding_function=embedding_func
                )
                logger.info(f"Retrieved existing collection: {self.collection_name}")
            except:
                collection = self.client.create_collection(
                    name=self.collection_name,
                    embedding_function=embedding_func,
                    metadata={"description": "Jarvis's implicit long-term memory"}
                )
                logger.info(f"Created new collection: {self.collection_name}")
            
            return collection
            
        except Exception as e:
            logger.error(f"Failed to initialize collection: {e}")
            raise
    
    def add_memory(
        self,
        text: str,
        user_id: str,
        session_id: str,
        memory_type: str,
        language: str,
        source_turn_id: Optional[str] = None,
        importance_score: Optional[float] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a new memory to the semantic store
        
        Args:
            text: The text content of the memory
            user_id: Unique identifier for the user
            session_id: Identifier for the conversation session
            memory_type: Type of memory (e.g., "user_preference", "stated_fact", etc.)
            language: Language of the content ("en" or "nl")
            source_turn_id: Optional ID of the conversation turn this memory came from
            importance_score: Optional score (1-5) indicating memory importance
            additional_metadata: Optional additional metadata to store
        
        Returns:
            memory_id: Unique identifier for the stored memory
        """
        try:
            # Generate a unique ID for the memory
            memory_id = f"mem_{int(time.time()*1000)}_{hash(text)%10000}"
            
            # Prepare metadata
            metadata = {
                "user_id": user_id,
                "session_id": session_id,
                "memory_type": memory_type,
                "language": language,
                "timestamp": datetime.utcnow().isoformat(),
                "source_turn_id": source_turn_id,
                "importance_score": importance_score
            }
            
            # Add any additional metadata
            if additional_metadata:
                metadata.update(additional_metadata)
            
            # Add the memory to ChromaDB
            self.collection.add(
                ids=[memory_id],
                documents=[text],
                metadatas=[metadata]
            )
            
            logger.info(f"Added memory {memory_id} of type {memory_type}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
            raise
    
    def query_memories(
        self,
        query_text: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        memory_type: Optional[str] = None,
        language: Optional[str] = None,
        min_importance_score: Optional[float] = None,
        n_results: int = 5,
        include_distances: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Query memories by semantic similarity with optional filters
        
        Args:
            query_text: The text to search for similar memories
            user_id: Optional filter for specific user's memories
            session_id: Optional filter for specific session
            memory_type: Optional filter for memory type
            language: Optional filter for language
            min_importance_score: Optional minimum importance score
            n_results: Number of results to return
            include_distances: Whether to include similarity distances in results
        
        Returns:
            List of matching memories with their metadata
        """
        try:
            # Build where clause for filtering
            where = {}
            if user_id:
                where["user_id"] = user_id
            if session_id:
                where["session_id"] = session_id
            if memory_type:
                where["memory_type"] = memory_type
            if language:
                where["language"] = language
            if min_importance_score is not None:
                where["importance_score"] = {"$gte": min_importance_score}
            
            # Query ChromaDB
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where or None,
                include=['metadatas', 'documents', 'distances'] if include_distances else ['metadatas', 'documents']
            )
            
            # Format results
            memories = []
            for i in range(len(results['ids'][0])):
                memory = {
                    "id": results['ids'][0][i],
                    "text": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i]
                }
                if include_distances:
                    memory["distance"] = results['distances'][0][i]
                memories.append(memory)
            
            return memories
            
        except Exception as e:
            logger.error(f"Failed to query memories: {e}")
            raise
    
    def get_memory_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific memory by its ID"""
        try:
            results = self.collection.get(
                ids=[memory_id],
                include=['metadatas', 'documents']
            )
            
            if results['ids']:
                return {
                    "id": results['ids'][0],
                    "text": results['documents'][0],
                    "metadata": results['metadatas'][0]
                }
            return None
            
        except Exception as e:
            logger.error(f"Failed to get memory {memory_id}: {e}")
            raise
    
    def update_memory_metadata(
        self,
        memory_id: str,
        metadata_updates: Dict[str, Any]
    ) -> bool:
        """
        Update metadata for a specific memory
        
        Args:
            memory_id: ID of the memory to update
            metadata_updates: Dictionary of metadata fields and values to update
        
        Returns:
            bool: True if successful, False if memory not found
        """
        try:
            # Get current memory
            memory = self.get_memory_by_id(memory_id)
            if not memory:
                return False
            
            # Update metadata
            new_metadata = memory['metadata']
            new_metadata.update(metadata_updates)
            
            # Update in ChromaDB
            self.collection.update(
                ids=[memory_id],
                metadatas=[new_metadata]
            )
            
            logger.info(f"Updated metadata for memory {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update memory metadata: {e}")
            raise
    
    def delete_memories(
        self,
        memory_ids: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        older_than: Optional[datetime] = None
    ) -> int:
        """
        Delete memories based on criteria
        
        Args:
            memory_ids: Optional list of specific memory IDs to delete
            user_id: Optional user ID to delete all memories for
            session_id: Optional session ID to delete all memories for
            older_than: Optional datetime to delete memories older than
        
        Returns:
            Number of memories deleted
        """
        try:
            if memory_ids:
                # Delete specific memories
                self.collection.delete(ids=memory_ids)
                return len(memory_ids)
            
            # Build where clause for filtering
            where = {}
            if user_id:
                where["user_id"] = user_id
            if session_id:
                where["session_id"] = session_id
            if older_than:
                where["timestamp"] = {"$lt": older_than.isoformat()}
            
            if where:
                # Get matching memories
                results = self.collection.get(
                    where=where,
                    include=['ids']
                )
                if results['ids']:
                    self.collection.delete(ids=results['ids'])
                    return len(results['ids'])
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to delete memories: {e}")
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the memory collection"""
        try:
            # Get all memories to compute stats
            results = self.collection.get()
            
            stats = {
                "total_memories": len(results['ids']),
                "memory_types": {},
                "languages": {},
                "users": set(),
                "sessions": set()
            }
            
            # Compute statistics
            for metadata in results['metadatas']:
                # Count memory types
                memory_type = metadata.get('memory_type')
                if memory_type:
                    stats['memory_types'][memory_type] = stats['memory_types'].get(memory_type, 0) + 1
                
                # Count languages
                language = metadata.get('language')
                if language:
                    stats['languages'][language] = stats['languages'].get(language, 0) + 1
                
                # Track unique users and sessions
                user_id = metadata.get('user_id')
                if user_id:
                    stats['users'].add(user_id)
                
                session_id = metadata.get('session_id')
                if session_id:
                    stats['sessions'].add(session_id)
            
            # Convert sets to counts
            stats['unique_users'] = len(stats['users'])
            stats['unique_sessions'] = len(stats['sessions'])
            del stats['users']
            del stats['sessions']
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            raise
    
    def peek_recent_memories(
        self,
        n: int = 5,
        user_id: Optional[str] = None,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get the n most recent memories (useful for debugging/monitoring)
        
        Args:
            n: Number of recent memories to retrieve
            user_id: Optional filter for specific user
            memory_type: Optional filter for memory type
        
        Returns:
            List of recent memories with their metadata
        """
        try:
            # Build where clause
            where = {}
            if user_id:
                where["user_id"] = user_id
            if memory_type:
                where["memory_type"] = memory_type
            
            # Get all memories and sort by timestamp
            results = self.collection.get(
                where=where or None,
                include=['metadatas', 'documents']
            )
            
            # Convert to list of dictionaries and sort by timestamp
            memories = []
            for i in range(len(results['ids'])):
                memories.append({
                    "id": results['ids'][i],
                    "text": results['documents'][i],
                    "metadata": results['metadatas'][i]
                })
            
            memories.sort(
                key=lambda x: x['metadata'].get('timestamp', ''),
                reverse=True
            )
            
            return memories[:n]
            
        except Exception as e:
            logger.error(f"Failed to peek recent memories: {e}")
            raise


# Example usage
if __name__ == "__main__":
    # Initialize the memory store
    memory_store = SemanticMemoryStore(
        host="localhost",
        port=8000
    )
    
    # Example: Add a memory
    memory_id = memory_store.add_memory(
        text="User prefers dark mode for all interfaces",
        user_id="user123",
        session_id="session456",
        memory_type="user_preference",
        language="en",
        importance_score=4.0
    )
    
    # Example: Query memories
    similar_memories = memory_store.query_memories(
        query_text="interface preferences",
        user_id="user123",
        language="en",
        n_results=3
    )
    
    # Print results
    print("\nQuery Results:")
    for memory in similar_memories:
        print(f"Memory: {memory['text']}")
        print(f"Metadata: {memory['metadata']}\n")