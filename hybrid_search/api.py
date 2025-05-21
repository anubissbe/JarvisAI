import os
import sys
try:
    from flask import Flask, request, jsonify
    FLASK_AVAILABLE = True
except ImportError:
    Flask = None; request = None; jsonify = None
    FLASK_AVAILABLE = False
    print("Warning: flask not installed; API endpoints disabled", file=sys.stderr)
from hybrid_search import HybridSearch
import requests

if FLASK_AVAILABLE:
    app = Flask(__name__)

# Configure connections via environment variables
neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
neo4j_password = os.environ.get('NEO4J_PASSWORD')
if neo4j_password is None:
    raise RuntimeError('NEO4J_PASSWORD environment variable not set')
milvus_host = os.environ.get('MILVUS_HOST', 'localhost')
milvus_port = os.environ.get('MILVUS_PORT', '19530')
ollama_url = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
searcher = HybridSearch(
    neo4j_uri=neo4j_uri,
    neo4j_user=neo4j_user,
    neo4j_password=neo4j_password,
    milvus_host=milvus_host,
    milvus_port=milvus_port,
    ollama_url=ollama_url
)

# def index():  # removed: redundant unguarded handler
if FLASK_AVAILABLE:
    @app.route('/')
    def index():
        return app.send_static_file('index.html')

# def search():  # removed: redundant unguarded handler
if FLASK_AVAILABLE:
    @app.route('/search', methods=['POST'])
    def search():
        data = request.get_json()
        query = data.get('query')
        kb_id = data.get('knowledge_base_id')
        top_k = data.get('top_k', 5)

        try:
            results = searcher.hybrid_search(query, kb_id, top_k)
            return jsonify({"results": results})
        except Exception as e:
            print(f"Search error: {str(e)}")
            return jsonify({"error": str(e), "results": []}), 500

# Add this route to test the API
# def status():  # removed: redundant unguarded handler
if FLASK_AVAILABLE:
    @app.route('/status', methods=['GET'])
    def status():
        try:
            # Test Neo4j connection
            with searcher.driver.session() as session:
                result = session.run("RETURN 'Connected!' as message")
                neo4j_status = result.single()["message"]

            return jsonify({
                "status": "ok",
                "neo4j": neo4j_status,
                "timestamp": searcher.get_timestamp()
            })
        except Exception as e:
            return jsonify({"status": "error", "error": str(e)}), 500
# Chat endpoint stub (disabled due to missing proper indentation)
if FLASK_AVAILABLE:
    @app.route('/chat', methods=['POST'])
    def chat():
        return jsonify({"error": "Chat endpoint not available"}), 501

if FLASK_AVAILABLE and __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
