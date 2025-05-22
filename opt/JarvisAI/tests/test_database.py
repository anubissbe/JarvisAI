import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add the parent directory to sys.path to allow imports from the project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestDatabase(unittest.TestCase):
    @patch('opt.JarvisAI.services.database.Database')
    def test_database_operations(self, mock_db):
        """Test database operations"""
        # Setup mock
        mock_instance = MagicMock()
        mock_db.return_value = mock_instance
        mock_instance.insert_conversation.return_value = True
        mock_instance.get_conversation_history.return_value = [{"role": "user", "content": "Hello"}]
        
        from opt.JarvisAI.services.database import Database
        
        # Test database operations
        db = Database()
        result = db.insert_conversation("user", "Hello")
        self.assertTrue(result)
        
        history = db.get_conversation_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["content"], "Hello")

if __name__ == '__main__':
    unittest.main()