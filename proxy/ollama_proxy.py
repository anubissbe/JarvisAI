from flask import Flask, request, jsonify
import os
import requests
from hybrid_search import HybridSearch

app = Flask(__name__)

# Connection details from environment variables
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "VerySecurePassword")
MILVUS_HOST = os.environ.get("MILVUS_HOST", "milvus-standalone")
MILVUS_PORT = os.environ.get("MILVUS_PORT", "19530")
OLLAMA_API_BASE_URL = os.environ.get("OLLAMA_API_BASE_URL", "http://ollama:11434")

try:
    hybrid_search = HybridSearch(
        neo4j_uri=NEO4J_URI,
        neo4j_user=NEO4J_USER,
        neo4j_password=NEO4J_PASSWORD,
        milvus_host=MILVUS_HOST,
        milvus_port=MILVUS_PORT,
        ollama_url=OLLAMA_API_BASE_URL,
    )
except Exception as exc:
    print(f"Failed to initialise HybridSearch: {exc}")
    hybrid_search = None

@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(path):
    print(f"Received request for /api/{path} (Method: {request.method})")
    
    # For chat requests, use hybrid search
    if path == 'chat':
        print(f"Processing chat request")
        return jsonify({"message": {"content": "This is a placeholder response since hybrid search is being fixed."}})
    
    # For all other requests, pass through to Ollama
    url = f"{OLLAMA_API_BASE_URL}/api/{path}"
    print(f"Proxying request to: {url} (Method: {request.method})")

    headers = {k: v for k, v in request.headers if k.lower() != 'host'}
    try:
        resp = requests.request(
            method=request.method,
            url=url,
            params=request.args,
            json=request.get_json(silent=True),
            headers=headers,
            timeout=300,
        )
    except requests.RequestException as exc:
        print(f"Request to Ollama failed: {exc}")
        return jsonify({"error": "Failed to contact Ollama"}), 502

    print(f"Response from {url}: status {resp.status_code}")
    return resp.content, resp.status_code, resp.headers.items()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
