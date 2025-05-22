#!/usr/bin/env python3
"""
Test script for Ollama Proxy service
"""

import os
import sys
import unittest
import json
import time
import threading
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, MagicMock

# Add parent directory to path to import module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the proxy module
try:
    from proxy.ollama_proxy import app, request_queue, ensure_workers
except ImportError:
    print("Error: Cannot import ollama_proxy module. Make sure you're running from the project root.")
    sys.exit(1)


class TestOllamaProxy(unittest.TestCase):
    """Tests for the Ollama Proxy service"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures before running tests"""
        # Configure the Flask test client
        app.config['TESTING'] = True
        cls.client = app.test_client()
        
        # Define test parameters
        cls.PROXY_URL = os.environ.get('PROXY_URL', 'http://localhost:11435')
        cls.OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
        
        # Check if Ollama is running (for integration tests)
        try:
            response = requests.get(f"{cls.OLLAMA_URL}/api/version", timeout=2)
            cls.ollama_available = response.status_code == 200
        except:
            cls.ollama_available = False
            print("Warning: Ollama server not available. Some integration tests will be skipped.")

    def setUp(self):
        """Set up test fixtures before each test"""
        # Clear the request queue
        while not request_queue.empty():
            try:
                request_queue.get_nowait()
                request_queue.task_done()
            except:
                break

    def test_health_endpoint(self):
        """Test the health check endpoint"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('status', data)
        
        # Basic format checks
        self.assertIn('queue_length', data)
        self.assertIn('active_workers', data)

    def test_metrics_endpoint(self):
        """Test the metrics endpoint"""
        response = self.client.get('/metrics')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Check required metrics
        self.assertIn('queue_length', data)
        self.assertIn('active_workers', data)
        self.assertIn('max_workers', data)

    @unittest.skipIf(not hasattr(TestOllamaProxy, 'ollama_available') or 
                    not TestOllamaProxy.ollama_available, 
                    "Ollama server not available")
    def test_proxy_version_endpoint(self):
        """Test proxying a request to Ollama's version endpoint"""
        # This is an integration test that requires Ollama to be running
        response = self.client.get('/api/version')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('version', data)

    def test_ensure_workers(self):
        """Test that ensure_workers creates worker threads"""
        # Mock the active_workers global
        with patch('proxy.ollama_proxy.active_workers', 0):
            with patch('proxy.ollama_proxy.MAX_CONCURRENT_REQUESTS', 3):
                with patch('proxy.ollama_proxy.RequestProcessor') as mock_processor:
                    # Call the function
                    ensure_workers()
                    
                    # Check that workers were created
                    self.assertEqual(mock_processor.call_count, 3)
                    
                    # Check that start was called on each worker
                    for call in mock_processor.mock_calls:
                        if '.start' in str(call):
                            mock_instance = call[0]
                            self.assertTrue(hasattr(mock_instance, 'start'))

    def test_request_priority(self):
        """Test request priority functionality"""
        from proxy.ollama_proxy import get_request_priority, PRIORITY
        
        # Test system operations (higher priority)
        self.assertEqual(get_request_priority('/api/tags', None), PRIORITY['system'])
        self.assertEqual(get_request_priority('/api/version', None), PRIORITY['system'])
        
        # Test other API endpoints
        self.assertEqual(get_request_priority('/api/embeddings', None), PRIORITY['embeddings'])
        self.assertEqual(get_request_priority('/api/chat', None), PRIORITY['chat'])
        self.assertEqual(get_request_priority('/api/generate', None), PRIORITY['completion'])
        self.assertEqual(get_request_priority('/api/pull', None), PRIORITY['pull'])
        
        # Test default priority
        self.assertEqual(get_request_priority('/unknown', None), PRIORITY['other'])

    @unittest.skipIf(not hasattr(TestOllamaProxy, 'ollama_available') or 
                    not TestOllamaProxy.ollama_available, 
                    "Ollama server not available")
    def test_concurrent_requests(self):
        """Test handling multiple concurrent requests"""
        # This is an integration test that requires Ollama to be running
        num_requests = 5
        
        # Function to make a request
        def make_request():
            response = requests.get(f"{self.PROXY_URL}/api/version")
            return response.status_code
        
        # Make concurrent requests
        with ThreadPoolExecutor(max_workers=num_requests) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            results = [future.result() for future in as_completed(futures)]
        
        # All requests should succeed
        self.assertEqual(results.count(200), num_requests)

    @patch('requests.get')
    def test_proxy_error_handling(self, mock_get):
        """Test error handling in the proxy"""
        # Mock a connection error
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        # Test that the proxy handles the error
        response = self.client.get('/api/version')
        
        # Should return a 500 error
        self.assertEqual(response.status_code, 500)
        
        # Response should contain error information
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['status'], 'error')


class TestProxyLoad(unittest.TestCase):
    """Load tests for the Ollama Proxy"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures before running tests"""
        # Define test parameters
        cls.PROXY_URL = os.environ.get('PROXY_URL', 'http://localhost:11435')
        cls.OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
        
        # Check if proxy is running
        try:
            response = requests.get(f"{cls.PROXY_URL}/health", timeout=2)
            cls.proxy_available = response.status_code == 200
        except:
            cls.proxy_available = False
            print("Warning: Ollama proxy not available. Load tests will be skipped.")

    @unittest.skipIf(not hasattr(TestProxyLoad, 'proxy_available') or 
                    not TestProxyLoad.proxy_available, 
                    "Ollama proxy not available")
    def test_load_version_endpoint(self):
        """Test the proxy under load with simple version requests"""
        num_requests = 20
        
        # Function to make a request
        def make_request():
            try:
                start_time = time.time()
                response = requests.get(f"{self.PROXY_URL}/api/version", timeout=10)
                end_time = time.time()
                return {
                    'status_code': response.status_code,
                    'response_time': end_time - start_time
                }
            except Exception as e:
                return {
                    'status_code': 0,
                    'error': str(e)
                }
        
        # Make concurrent requests
        with ThreadPoolExecutor(max_workers=num_requests) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            results = [future.result() for future in as_completed(futures)]
        
        # Calculate stats
        success_count = sum(1 for r in results if r['status_code'] == 200)
        if success_count > 0:
            response_times = [r['response_time'] for r in results if r['status_code'] == 200]
            avg_response_time = sum(response_times) / len(response_times)
            
            print(f"\nLoad test results:")
            print(f"Successful requests: {success_count}/{num_requests}")
            print(f"Average response time: {avg_response_time:.4f} seconds")
            
            # All requests should succeed
            self.assertEqual(success_count, num_requests)


if __name__ == '__main__':
    # Run unit tests
    unittest.main()