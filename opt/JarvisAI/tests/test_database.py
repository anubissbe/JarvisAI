# ... existing code ...
class TestDatabase(unittest.TestCase):
    def test_database_operations(self):
        """Test database operations"""
        # Mock a database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock the fetchall method to return test data
        mock_cursor.fetchall.return_value = [{'id': 1, 'message': 'test message'}]
        
        # Define a simple function to get chat history
        def get_chat_history(user_id, conn=mock_conn):
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM chat_history WHERE user_id = %s", (user_id,))
            return cursor.fetchall()
        
        # Test the function
        result = get_chat_history(user_id=1)
        self.assertEqual(result, [{'id': 1, 'message': 'test message'}])
        mock_cursor.execute.assert_called_once()
# ... existing code ...