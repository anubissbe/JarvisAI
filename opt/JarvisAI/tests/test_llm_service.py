import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add the parent directory to sys.path to allow imports from the project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestLLMService(unittest.TestCase):
    @patch('opt.JarvisAI.services.llm_service.openai.ChatCompletion.create')
    def test_openai_completion(self, mock_create):
        """Test OpenAI completion functionality"""
        # Setup mock
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Test response"
        mock_create.return_value = mock_response
        
        from opt.JarvisAI.services.llm_service import generate_response
        
        # Test the function
        response = generate_response("Test prompt")
        self.assertEqual(response, "Test response")
        mock_create.assert_called_once()

if __name__ == '__main__':
    unittest.main()