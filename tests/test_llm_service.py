import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestLLMService(unittest.TestCase):
    @patch('services.llm_service.OpenAI')
    def test_openai_completion(self, mock_openai):
        """Test OpenAI completion functionality"""
        # Setup the mock
        mock_instance = MagicMock()
        mock_openai.return_value = mock_instance
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "This is a test response"
        mock_instance.chat.completions.create.return_value = mock_response
        
        # Import after patching
        from services.llm_service import get_completion
        
        # Test the function
        response = get_completion("Test prompt")
        self.assertEqual(response, "This is a test response")
        mock_instance.chat.completions.create.assert_called_once()

if __name__ == '__main__':
    unittest.main()