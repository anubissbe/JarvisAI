#!/usr/bin/env python3
"""
Ollama API Proxy for JarvisAI
This service proxies requests to the Ollama API, providing:
1. Rate limiting to prevent Ollama from being overwhelmed
2. Request queuing for a smoother experience under load
3. Concurrent request handling with prioritization
4. Streaming response support
"""

import os
import json
import time
import logging
import threading
import queue
from typing import Dict, Any, List, Optional
import requests
from flask import Flask, request, Response, stream_with_context

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ollama_proxy')

# Configuration
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
MAX_CONCURRENT_REQUESTS = int(os.environ.get('MAX_CONCURRENT_REQUESTS', '3'))
QUEUE_TIMEOUT_SECONDS = int(os.environ.get('QUEUE_TIMEOUT_SECONDS', '300'))
PORT = int(os.environ.get('PORT', '11435'))

# Initialize Flask app
app = Flask(__name__)

# Request queue and worker management
request_queue = queue.PriorityQueue()
active_workers = 0
queue_lock = threading.Lock()

# Priority constants (lower number = higher priority)
PRIORITY = {
    'system': 1,
    'completion': 2,
    'embeddings': 3,
    'chat': 4,
    'pull': 5,
    'other': 10
}

class RequestProcessor(threading.Thread):
    """Worker thread to process Ollama API requests"""
    
    def __init__(self, worker_id: int):
        super().__init__(daemon=True)
        self.worker_id = worker_id
        self.active = True
    
    def run(self):
        global active_workers
        logger.info(f"Worker {self.worker_id} started")
        
        while self.active:
            try:
                # Get a request from the queue with timeout
                priority, timestamp, req_data = request_queue.get(timeout=5)
                
                # Process the request
                self._process_request(req_data)
                
                # Mark task as done
                request_queue.task_done()
                
            except queue.Empty:
                # No requests in queue, just continue waiting
                continue
            except Exception as e:
                logger.error(f"Worker {self.worker_id} encountered an error: {e}")
                # If we had a request, mark it as done
                if 'req_data' in locals():
                    request_queue.task_done()
        
        # Decrement active workers count when exiting
        with queue_lock:
            active_workers -= 1
        logger.info(f"Worker {self.worker_id} stopped")
    
    def _process_request(self, req_data: Dict[str, Any]):
        """Process a request to the Ollama API"""
        method = req_data['method']
        path = req_data['path']
        headers = req_data['headers']
        data = req_data.get('data')
        response_callback = req_data['response_callback']
        
        logger.info(f"Worker {self.worker_id} processing {method} {path}")
        
        try:
            # Prepare the request to Ollama
            url = f"{OLLAMA_BASE_URL}{path}"
            
            # Make the request to Ollama
            if method == 'GET':
                response = requests.get(url, headers=headers, stream=True)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, stream=True)
            else:
                # Handle other HTTP methods if needed
                response = requests.request(method, url, headers=headers, json=data, stream=True)
            
            # Send the response back to the client
            response_callback(response)
            
        except Exception as e:
            logger.error(f"Error processing request to {path}: {e}")
            # Send error response
            error_response = {
                "error": f"Proxy error: {str(e)}",
                "status": "error"
            }
            response_callback(error_response)


def get_request_priority(path: str, data: Optional[Dict[str, Any]]) -> int:
    """Determine the priority of a request based on its path and data"""
    # Check for system operations (higher priority)
    if '/api/tags' in path or '/api/version' in path:
        return PRIORITY['system']
    
    # Check other API endpoints
    if '/api/embeddings' in path:
        return PRIORITY['embeddings']
    elif '/api/chat' in path:
        return PRIORITY['chat']
    elif '/api/generate' in path:
        return PRIORITY['completion']
    elif '/api/pull' in path:
        return PRIORITY['pull']
    
    # Default priority for other requests
    return PRIORITY['other']


def ensure_workers():
    """Ensure we have the right number of worker threads running"""
    global active_workers
    
    with queue_lock:
        current_workers = active_workers
        needed_workers = MAX_CONCURRENT_REQUESTS - current_workers
        
        if needed_workers > 0:
            logger.info(f"Starting {needed_workers} new worker threads")
            for i in range(needed_workers):
                worker = RequestProcessor(current_workers + i + 1)
                worker.start()
                active_workers += 1


@app.route('/', defaults={'path': ''}, methods=['GET'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(path):
    """Main proxy route handler"""
    # Create the full path
    if not path.startswith('/'):
        path = '/' + path
    
    # Get request data for POST requests
    data = None
    if request.method == 'POST' and request.is_json:
        data = request.get_json()
    
    # Determine request priority
    priority = get_request_priority(path, data)
    timestamp = time.time()  # For breaking ties in priority
    
    # Create a response queue for this specific request
    response_queue = queue.Queue()
    
    def response_callback(response):
        """Callback to handle the response from Ollama"""
        response_queue.put(response)
    
    # Package the request
    req_data = {
        'method': request.method,
        'path': path,
        'headers': {k: v for k, v in request.headers.items() if k not in ['Host', 'Content-Length']},
        'data': data,
        'response_callback': response_callback
    }
    
    # Add to the processing queue
    request_queue.put((priority, timestamp, req_data))
    
    # Ensure we have enough workers
    ensure_workers()
    
    # Wait for the response with timeout
    try:
        response_data = response_queue.get(timeout=QUEUE_TIMEOUT_SECONDS)
        
        if isinstance(response_data, dict):
            # It's an error response
            return response_data, 500
        
        # Handle streamed responses
        def generate():
            for chunk in response_data.iter_content(chunk_size=4096):
                yield chunk
            
        # Create a Flask response with the same status code and headers
        resp = Response(stream_with_context(generate()))
        resp.status_code = response_data.status_code
        
        # Copy headers from original response
        for key, value in response_data.headers.items():
            if key.lower() not in ('content-length', 'transfer-encoding', 'connection'):
                resp.headers[key] = value
                
        return resp
        
    except queue.Empty:
        return {"error": "Request timed out in queue", "status": "timeout"}, 504


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check if Ollama is responsive
        response = requests.get(f"{OLLAMA_BASE_URL}/api/version", timeout=5)
        if response.status_code == 200:
            queue_size = request_queue.qsize()
            return {
                "status": "healthy",
                "ollama_status": "connected",
                "queue_length": queue_size,
                "active_workers": active_workers,
                "ollama_version": response.json().get("version", "unknown")
            }
        else:
            return {
                "status": "degraded",
                "ollama_status": f"error: {response.status_code}",
                "queue_length": request_queue.qsize(),
                "active_workers": active_workers
            }, 200
    except Exception as e:
        return {
            "status": "unhealthy", 
            "error": str(e),
            "queue_length": request_queue.qsize(),
            "active_workers": active_workers
        }, 500


@app.route('/metrics', methods=['GET'])
def metrics():
    """Metrics endpoint for monitoring"""
    return {
        "queue_length": request_queue.qsize(),
        "active_workers": active_workers,
        "max_workers": MAX_CONCURRENT_REQUESTS
    }


if __name__ == '__main__':
    logger.info(f"Starting Ollama Proxy on port {PORT}")
    logger.info(f"Proxying to Ollama at {OLLAMA_BASE_URL}")
    logger.info(f"Max concurrent requests: {MAX_CONCURRENT_REQUESTS}")
    
    # Initialize worker threads
    ensure_workers()
    
    # Start the Flask app
    app.run(host='0.0.0.0', port=PORT, threaded=True)