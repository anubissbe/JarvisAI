from flask import Flask, request, jsonify
import requests
from hybrid_search import HybridSearch

app = Flask(__name__)
hybrid_search = HybridSearch()

@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(path):
    print(f"Received request for /api/{path} (Method: {request.method})")
    
    # For chat requests, use hybrid search
    if path == 'chat':
        print(f"Processing chat request")
        return jsonify({"message": {"content": "This is a placeholder response since hybrid search is being fixed."}})
    
    # For all other requests, pass through to Ollama
    url = f"http://ollama:11434/api/{path}"
    print(f"Proxying request to: {url} (Method: {request.method})")
    
    # Forward the request
    if request.method == 'GET':
        resp = requests.get(url, params=request.args)
    else:
        resp = requests.post(url, json=request.json)
    
    print(f"Response from {url}: status {resp.status_code}")
    return resp.content, resp.status_code, resp.headers.items()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
