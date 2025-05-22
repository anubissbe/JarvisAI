import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestDatabase(unittest.TestCase):
    def setUp(self):
        # Create a mock database module
        self.mock_db = MagicMock()
        self.mock_db.get_chat_history = MagicMock(return_value=[{'id': 1, 'message': 'test message'}])
        sys.modules['database'] = self.mock_db
        
    def test_database_operations(self):
        """Test database operations"""
        # Import the mocked module
        from database import get_chat_history
        
        # Test the function
        result = get_chat_history(user_id=1)
        self.assertEqual(result, [{'id': 1, 'message': 'test message'}])
        self.mock_db.get_chat_history.assert_called_once_with(user_id=1)

if __name__ == '__main__':
    unittest.main()