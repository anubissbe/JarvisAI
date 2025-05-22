import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestAPIEndpoints(unittest.TestCase):
    @patch('services.llm_service.get_completion')
    def test_chat_endpoint(self, mock_get_completion):
        """Test the chat endpoint"""
        mock_get_completion.return_value = "This is a test response"
        
        # Import after patching
        from api.app import app
        
        # Create a test client
        client = app.test_client()
        
        # Send a request to the endpoint
        response = client.post('/api/chat', 
                              data=json.dumps({'message': 'Hello'}),
                              content_type='application/json')
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['response'], "This is a test response")
        mock_get_completion.assert_called_once_with('Hello')

if __name__ == '__main__':
    unittest.main()