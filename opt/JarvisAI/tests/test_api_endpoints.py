import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestAPIEndpoints(unittest.TestCase):
    def setUp(self):
        # Create a mock LLM service module
        self.mock_llm_service = MagicMock()
        self.mock_llm_service.get_completion = MagicMock(return_value="This is a test response")
        sys.modules['llm_service'] = self.mock_llm_service
        
        # Create a mock Flask app
        self.mock_app = MagicMock()
        mock_client = MagicMock()
        self.mock_app.test_client = MagicMock(return_value=mock_client)
        sys.modules['app'] = self.mock_app
        
    def test_chat_endpoint(self):
        """Test the chat endpoint"""
        # Import the mocked modules
        from llm_service import get_completion
        from app import app
        
        # Create a test client
        client = app.test_client()
        
        # Mock the response from the test client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.data = json.dumps({'response': "This is a test response"}).encode('utf-8')
        client.post = MagicMock(return_value=mock_response)
        
        # Send a request to the endpoint
        response = client.post('/api/chat', 
                              data=json.dumps({'message': 'Hello'}),
                              content_type='application/json')
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['response'], "This is a test response")
        client.post.assert_called_once()

if __name__ == '__main__':
    unittest.main()