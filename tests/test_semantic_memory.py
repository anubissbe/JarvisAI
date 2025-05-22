#!/usr/bin/env python3
"""
Tests for the Semantic Memory Store
"""

import os
import sys
import unittest
import json
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add parent directory to path to import module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the semantic memory module
try:
    from semantic_memory.memory_store import SemanticMemoryStore
except ImportError:
    print("Error: Cannot import semantic_memory module. Make sure you're running from the project root.")
    sys.exit(1)


class TestSemanticMemoryStore(unittest.TestCase):
    """Tests for the SemanticMemoryStore class"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures before running tests"""
        # Check if ChromaDB is running
        try:
            cls.memory_store = SemanticMemoryStore(
                host="localhost",
                port=8000,
                collection_name="test_jarvis_ltm"
            )
            cls.chromadb_available = True
        except:
            cls.chromadb_available = False
            print("Warning: ChromaDB not available. Integration tests will be skipped.")

    def setUp(self):
        """Set up test fixtures before each test"""
        if not hasattr(self, 'chromadb_available') or not self.chromadb_available:
            self.skipTest("ChromaDB not available")
        
        # Clear test collection before each test
        self.memory_store.delete_memories()

    def test_add_memory(self):
        """Test adding a memory to the store"""
        memory_id = self.memory_store.add_memory(
            text="User prefers dark mode for all interfaces",
            user_id="test_user",
            session_id="test_session",
            memory_type="user_preference",
            language="en",
            importance_score=4.0
        )
        
        # Verify memory was added
        memory = self.memory_store.get_memory_by_id(memory_id)
        self.assertIsNotNone(memory)
        self.assertEqual(memory['text'], "User prefers dark mode for all interfaces")
        self.assertEqual(memory['metadata']['user_id'], "test_user")
        self.assertEqual(memory['metadata']['importance_score'], 4.0)

    def test_query_memories(self):
        """Test querying memories"""
        # Add test memories
        self.memory_store.add_memory(
            text="User prefers dark mode for all interfaces",
            user_id="test_user",
            session_id="test_session",
            memory_type="user_preference",
            language="en",
            importance_score=4.0
        )
        self.memory_store.add_memory(
            text="User's favorite programming language is Python",
            user_id="test_user",
            session_id="test_session",
            memory_type="user_preference",
            language="en",
            importance_score=3.0
        )
        
        # Query for interface-related memories
        results = self.memory_store.query_memories(
            query_text="interface preferences",
            user_id="test_user",
            n_results=2
        )
        
        # Verify results
        self.assertEqual(len(results), 2)
        # The dark mode memory should be more relevant to "interface preferences"
        self.assertIn("dark mode", results[0]['text'].lower())

    def test_memory_filters(self):
        """Test memory filtering by various criteria"""
        # Add memories with different attributes
        self.memory_store.add_memory(
            text="Dit is een Nederlandse herinnering",
            user_id="user1",
            session_id="session1",
            memory_type="fact",
            language="nl",
            importance_score=3.0
        )
        self.memory_store.add_memory(
            text="This is an English memory",
            user_id="user1",
            session_id="session1",
            memory_type="fact",
            language="en",
            importance_score=4.0
        )
        
        # Test language filter
        dutch_results = self.memory_store.query_memories(
            query_text="herinnering",
            language="nl"
        )
        self.assertEqual(len(dutch_results), 1)
        self.assertEqual(dutch_results[0]['metadata']['language'], "nl")
        
        # Test importance score filter
        important_results = self.memory_store.query_memories(
            query_text="memory",
            min_importance_score=4.0
        )
        self.assertEqual(len(important_results), 1)
        self.assertEqual(important_results[0]['metadata']['importance_score'], 4.0)

    def test_update_memory_metadata(self):
        """Test updating memory metadata"""
        # Add a memory
        memory_id = self.memory_store.add_memory(
            text="Initial memory",
            user_id="test_user",
            session_id="test_session",
            memory_type="note",
            language="en",
            importance_score=2.0
        )
        
        # Update metadata
        success = self.memory_store.update_memory_metadata(
            memory_id,
            {"importance_score": 4.0, "memory_type": "important_note"}
        )
        
        # Verify update
        self.assertTrue(success)
        memory = self.memory_store.get_memory_by_id(memory_id)
        self.assertEqual(memory['metadata']['importance_score'], 4.0)
        self.assertEqual(memory['metadata']['memory_type'], "important_note")

    def test_delete_memories(self):
        """Test deleting memories"""
        # Add test memories
        memory_id1 = self.memory_store.add_memory(
            text="Memory to delete 1",
            user_id="user1",
            session_id="session1",
            memory_type="test",
            language="en"
        )
        memory_id2 = self.memory_store.add_memory(
            text="Memory to delete 2",
            user_id="user1",
            session_id="session1",
            memory_type="test",
            language="en"
        )
        
        # Delete specific memory
        deleted_count = self.memory_store.delete_memories(
            memory_ids=[memory_id1]
        )
        self.assertEqual(deleted_count, 1)
        
        # Verify memory was deleted
        memory = self.memory_store.get_memory_by_id(memory_id1)
        self.assertIsNone(memory)
        
        # Delete by user_id
        deleted_count = self.memory_store.delete_memories(
            user_id="user1"
        )
        self.assertEqual(deleted_count, 1)  # Should delete memory_id2
        
        # Verify all memories deleted
        stats = self.memory_store.get_collection_stats()
        self.assertEqual(stats['total_memories'], 0)

    def test_collection_stats(self):
        """Test getting collection statistics"""
        # Add test memories
        self.memory_store.add_memory(
            text="English memory 1",
            user_id="user1",
            session_id="session1",
            memory_type="fact",
            language="en"
        )
        self.memory_store.add_memory(
            text="English memory 2",
            user_id="user1",
            session_id="session2",
            memory_type="preference",
            language="en"
        )
        self.memory_store.add_memory(
            text="Nederlandse herinnering",
            user_id="user2",
            session_id="session3",
            memory_type="fact",
            language="nl"
        )
        
        # Get stats
        stats = self.memory_store.get_collection_stats()
        
        # Verify stats
        self.assertEqual(stats['total_memories'], 3)
        self.assertEqual(stats['unique_users'], 2)
        self.assertEqual(stats['unique_sessions'], 3)
        self.assertEqual(stats['languages']['en'], 2)
        self.assertEqual(stats['languages']['nl'], 1)
        self.assertEqual(stats['memory_types']['fact'], 2)
        self.assertEqual(stats['memory_types']['preference'], 1)

    def test_peek_recent_memories(self):
        """Test retrieving recent memories"""
        # Add memories with different timestamps
        for i in range(3):
            self.memory_store.add_memory(
                text=f"Memory {i}",
                user_id="test_user",
                session_id=f"session{i}",
                memory_type="test",
                language="en"
            )
            time.sleep(0.1)  # Ensure different timestamps
        
        # Get recent memories
        recent = self.memory_store.peek_recent_memories(n=2)
        
        # Verify order and count
        self.assertEqual(len(recent), 2)
        self.assertEqual(recent[0]['text'], "Memory 2")
        self.assertEqual(recent[1]['text'], "Memory 1")


class TestSemanticMemoryStoreMocked(unittest.TestCase):
    """Tests using mocked ChromaDB client for scenarios difficult to test with real DB"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_client = MagicMock()
        self.mock_collection = MagicMock()
        self.mock_client.get_collection.return_value = self.mock_collection
        
        with patch('chromadb.HttpClient', return_value=self.mock_client):
            self.memory_store = SemanticMemoryStore()

    def test_error_handling_add_memory(self):
        """Test error handling when adding memory fails"""
        self.mock_collection.add.side_effect = Exception("Simulated error")
        
        with self.assertRaises(Exception):
            self.memory_store.add_memory(
                text="Test memory",
                user_id="user1",
                session_id="session1",
                memory_type="test",
                language="en"
            )

    def test_error_handling_query(self):
        """Test error handling when query fails"""
        self.mock_collection.query.side_effect = Exception("Simulated error")
        
        with self.assertRaises(Exception):
            self.memory_store.query_memories(
                query_text="test query"
            )


if __name__ == '__main__':
    unittest.main()