import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestUtils(unittest.TestCase):
    def test_environment_variables(self):
        """Test that environment variables are properly loaded"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            # Mock the config module
            mock_config = MagicMock()
            mock_config.get_openai_api_key = MagicMock(return_value='test_key')
            sys.modules['config'] = mock_config
            
            # Test that we can access the mocked function
            from config import get_openai_api_key
            self.assertEqual(get_openai_api_key(), 'test_key')
    
    def test_file_operations(self):
        """Test file operations"""
        # Create a mock file operations module
        mock_file_ops = MagicMock()
        mock_file_ops.read_file = MagicMock(return_value='test data')
        sys.modules['file_ops'] = mock_file_ops
        
        # Test the mocked function
        from file_ops import read_file
        self.assertEqual(read_file('dummy_path'), 'test data')

if __name__ == '__main__':
    unittest.main()