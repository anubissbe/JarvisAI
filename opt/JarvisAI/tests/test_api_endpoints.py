# ... existing code ...
class TestAPIEndpoints(unittest.TestCase):
    def test_chat_endpoint(self):
        """Test the chat endpoint"""
        # Create a mock Flask app
        mock_app = MagicMock()
        mock_client = MagicMock()
        mock_app.test_client.return_value = mock_client
        
        # Mock the response from the test client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.data = json.dumps({'response': "This is a test response"}).encode('utf-8')
        mock_client.post.return_value = mock_response
        
        # Send a request to the endpoint
        response = mock_client.post('/api/chat', 
                              data=json.dumps({'message': 'Hello'}),
                              content_type='application/json')
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['response'], "This is a test response")
        mock_client.post.assert_called_once()
# ... existing code ...