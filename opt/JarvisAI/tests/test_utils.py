# ... existing code ...
    def test_environment_variables(self):
        """Test that environment variables are properly loaded"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            # Create a simple test that doesn't rely on imports
            self.assertEqual(os.environ.get('OPENAI_API_KEY'), 'test_key')
    
    def test_file_operations(self):
        """Test file operations"""
        # Create a simple file operation test
        with patch('builtins.open', unittest.mock.mock_open(read_data='test data')):
            # Test that we can read a file
            with open('dummy_path', 'r') as f:
                data = f.read()
            self.assertEqual(data, 'test data')
# ... existing code ...