import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestUtils(unittest.TestCase):
    def test_environment_variables(self):
        """Test that environment variables are properly loaded"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            from utils.config import get_openai_api_key
            self.assertEqual(get_openai_api_key(), 'test_key')
    
    def test_file_operations(self):
        """Test file operations"""
        with patch('builtins.open', unittest.mock.mock_open(read_data='test data')):
            from utils.file_ops import read_file
            self.assertEqual(read_file('dummy_path'), 'test data')

if __name__ == '__main__':
    unittest.main()