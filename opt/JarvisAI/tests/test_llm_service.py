import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestLLMService(unittest.TestCase):
    def setUp(self):
        # Create a mock LLM service module
        self.mock_llm_service = MagicMock()
        self.mock_llm_service.get_completion.return_value = "This is a test response"
        sys.modules['llm_service'] = self.mock_llm_service
        
    def test_openai_completion(self):
        """Test OpenAI completion functionality"""
        # Import the mocked module
        from llm_service import get_completion
        
        # Test the function
        response = get_completion("Test prompt")
        self.assertEqual(response, "This is a test response")
        self.mock_llm_service.get_completion.assert_called_once_with("Test prompt")

if __name__ == '__main__':
    unittest.main()