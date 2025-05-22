import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json

# Add the parent directory to sys.path to allow imports from the project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestAPIEndpoints(unittest.TestCase):
    @patch('opt.JarvisAI.services.llm_service.generate_response')
    def test_chat_endpoint(self, mock_generate):
        """Test the chat endpoint"""
        # Setup mock
        mock_generate.return_value = "Test response"
        
        from opt.JarvisAI.api.endpoints import chat_endpoint
        
        # Create a mock request
        mock_request = MagicMock()
        mock_request.json = {"message": "Hello"}
        
        # Test the endpoint
        response = chat_endpoint(mock_request)
        self.assertEqual(response["response"], "Test response")
        mock_generate.assert_called_once_with("Hello")

if __name__ == '__main__':
    unittest.main()