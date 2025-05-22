import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestDatabase(unittest.TestCase):
    @patch('services.database.get_db_connection')
    def test_database_operations(self, mock_get_db_connection):
        """Test database operations"""
        # Setup the mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db_connection.return_value = mock_conn
        
        # Mock the fetchall method to return test data
        mock_cursor.fetchall.return_value = [{'id': 1, 'message': 'test message'}]
        
        # Import after patching
        from services.database import get_chat_history
        
        # Test the function
        result = get_chat_history(user_id=1)
        self.assertEqual(result, [{'id': 1, 'message': 'test message'}])
        mock_cursor.execute.assert_called_once()

if __name__ == '__main__':
    unittest.main()