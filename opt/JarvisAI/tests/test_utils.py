import unittest
import os
import sys

# Add the parent directory to sys.path to allow imports from the project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestUtils(unittest.TestCase):
    def test_environment_variables(self):
        """Test that environment variables are properly loaded"""
        from opt.JarvisAI.utils.config import get_openai_api_key
        # Mock environment variable
        os.environ['OPENAI_API_KEY'] = 'test_key'
        self.assertEqual(get_openai_api_key(), 'test_key')

    def test_file_operations(self):
        """Test file operations"""
        from opt.JarvisAI.utils.file_ops import read_file
        # Create a test file
        with open('test_file.txt', 'w') as f:
            f.write('test content')
        
        # Test reading the file
        content = read_file('test_file.txt')
        self.assertEqual(content, 'test content')
        
        # Clean up
        os.remove('test_file.txt')

if __name__ == '__main__':
    unittest.main()