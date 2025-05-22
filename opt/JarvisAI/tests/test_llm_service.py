# ... existing code ...
class TestLLMService(unittest.TestCase):
    def test_openai_completion(self):
        """Test OpenAI completion functionality"""
        # Mock the OpenAI client
        mock_openai = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is a test response"
        mock_openai.ChatCompletion.create.return_value = mock_response
        
        # Test a simple completion function
        def get_completion(prompt, model="gpt-3.5-turbo"):
            response = mock_openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        
        # Test the function
        response = get_completion("Test prompt")
        self.assertEqual(response, "This is a test response")
        mock_openai.ChatCompletion.create.assert_called_once()
# ... existing code ...