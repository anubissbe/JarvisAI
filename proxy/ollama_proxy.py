from flask import Flask, request, Response, jsonify, send_from_directory
import requests
import json
import sys
import os
import traceback
from datetime import datetime

# Add the hybrid_search directory to the path
sys.path.append('/opt/jarvis/hybrid_search')
from hybrid_search import HybridSearch

app = Flask(__name__, static_folder='static')

# Configuration
OLLAMA_API = "http://ollama:11434/api"
KNOWLEDGE_BASE_ID = os.environ.get("KNOWLEDGE_BASE_ID", "96c3b9a4-10c1-400c-9d22-3e71cb8ed7fb")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "Loebas0128")

# Initialize the hybrid search
print("Initializing HybridSearch with Neo4j connection...")
try:
    searcher = HybridSearch(
        neo4j_uri="bolt://neo4j:7687",  # Using Docker service name
        neo4j_user="neo4j",
        neo4j_password=NEO4J_PASSWORD,
        milvus_host="milvus-standalone",  # Using Docker service name
        milvus_port="19530",
        ollama_url="http://ollama:11434"
    )
    print("HybridSearch initialized successfully")
except Exception as e:
    print(f"Failed to initialize HybridSearch: {str(e)}")
    print(traceback.format_exc())
    searcher = None

# Store conversation history
conversations = {}

@app.route('/api/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(subpath):
    """Proxy all requests to Ollama API, but intercept chat and completions"""
    target_url = f"{OLLAMA_API}/{subpath}"
    
    print(f"Received request for /api/{subpath} (Method: {request.method})")
    
    # Special handling for model operations - pass through directly
    if subpath in ['pull', 'create', 'delete', 'list', 'show', 'copy', 'tags']:
        print(f"Model operation detected: {subpath} - passing through directly")
        return direct_proxy(target_url, request)
    
    # Special handling for embeddings - pass through directly
    if subpath == 'embeddings':
        print("Embeddings request detected - passing through directly")
        return direct_proxy(target_url, request)
    
    # Special handling for chat and completions
    if request.method == 'POST' and (subpath == 'chat' or subpath == 'generate'):
        if subpath == 'chat':
            # Check if this is a model loading request
            try:
                data = request.get_json(silent=True)
                if data and 'model' in data and len(data.get('messages', [])) == 0:
                    print(f"Model loading detected for: {data.get('model')} - passing through directly")
                    return direct_proxy(target_url, request)
            except Exception as e:
                print(f"Error checking if request is model loading: {str(e)}")
        
        # Regular chat/generate request - enhance with knowledge
        return enhanced_request(subpath, request)
    
    # For all other requests, just proxy directly
    return direct_proxy(target_url, request)

def enhanced_request(endpoint, original_request):
    """Enhance chat/completion requests with hybrid search context"""
    try:
        # Get the request data
        data = original_request.get_json()
        request_id = datetime.now().strftime("%Y%m%d%H%M%S")
        print(f"[{request_id}] Processing {endpoint} request")
        
        # Extract the query (different structure for chat vs generate)
        if endpoint == 'chat':
            # Extract the last user message
            messages = data.get('messages', [])
            if not messages:
                print(f"[{request_id}] No messages found in chat request")
                return direct_proxy(f"{OLLAMA_API}/{endpoint}", original_request)
                
            last_user_msg = None
            for msg in reversed(messages):
                if msg.get('role') == 'user':
                    last_user_msg = msg.get('content')
                    break
                    
            if not last_user_msg:
                print(f"[{request_id}] No user message found in chat request")
                return direct_proxy(f"{OLLAMA_API}/{endpoint}", original_request)
                
            query = last_user_msg
        else:  # generate endpoint
            query = data.get('prompt', '')
            
        if not query:
            print(f"[{request_id}] No query found in request")
            return direct_proxy(f"{OLLAMA_API}/{endpoint}", original_request)
        
        print(f"[{request_id}] Extracted query: {query[:100]}{'...' if len(query) > 100 else ''}")
            
        # Perform hybrid search if searcher is available
        if searcher:
            print(f"[{request_id}] Performing hybrid search for query")
            try:
                search_results = searcher.hybrid_search(
                    query_text=query,
                    knowledge_base_id=KNOWLEDGE_BASE_ID,
                    top_k=3
                )
                print(f"[{request_id}] Found {len(search_results)} relevant documents")
            except Exception as e:
                print(f"[{request_id}] Error during hybrid search: {str(e)}")
                print(traceback.format_exc())
                search_results = []
        else:
            print(f"[{request_id}] Searcher not available, skipping hybrid search")
            search_results = []
        
        # If no results, just proxy the original request
        if not search_results:
            print(f"[{request_id}] No search results found, forwarding original request")
            return direct_proxy(f"{OLLAMA_API}/{endpoint}", original_request)
            
        # Format context from search results
        context_pieces = []
        for r in search_results:
            source_type = r.get('source', 'unknown')
            title = r.get('title', 'Unknown Document')
            
            context = f"Source: {title} ({source_type})\n"
            
            if "concept" in r and "concept_description" in r:
                context += f"Concept: {r['concept']} - {r['concept_description']}\n"
                
            if "content" in r:
                context += r.get('content', '')
                
            context_pieces.append(context)
        
        context_text = "\n\n---\n\n".join(context_pieces)
        print(f"[{request_id}] Created context from {len(context_pieces)} sources")
        
        # Create enhanced request
        enhanced_data = data.copy()
        
        if endpoint == 'chat':
            # Add a system message with the context or enhance existing one
            system_msg_idx = None
            for i, msg in enumerate(enhanced_data.get('messages', [])):
                if msg.get('role') == 'system':
                    system_msg_idx = i
                    break
                    
            context_prefix = "I've found some information that might help answer the question:\n\n"
            context_suffix = "\n\nUse this information if relevant to answer the user's question."
            
            if system_msg_idx is not None:
                # Enhance existing system message
                current_content = enhanced_data['messages'][system_msg_idx].get('content', '')
                enhanced_data['messages'][system_msg_idx]['content'] = (
                    f"{current_content}\n\n{context_prefix}{context_text}{context_suffix}"
                )
                print(f"[{request_id}] Enhanced existing system message")
            else:
                # Add new system message at the beginning
                enhanced_data['messages'].insert(0, {
                    'role': 'system',
                    'content': f"{context_prefix}{context_text}{context_suffix}"
                })
                print(f"[{request_id}] Added new system message with context")
        else:  # generate endpoint
            # For generate, prepend the context to the prompt
            context_wrapper = (
                "I've found some information that might help answer your question:\n\n"
                f"{context_text}\n\n"
                "Using this information, please answer the following query:\n\n"
            )
            enhanced_data['prompt'] = context_wrapper + enhanced_data.get('prompt', '')
            print(f"[{request_id}] Enhanced prompt with context")
        
        # Forward the enhanced request to Ollama
        print(f"[{request_id}] Sending enhanced request to Ollama")
        response = requests.post(
            f"{OLLAMA_API}/{endpoint}",
            json=enhanced_data,
            headers={key: value for key, value in original_request.headers if key != 'Host'},
            stream=original_request.environ.get('HTTP_TRANSFER_ENCODING') == 'chunked'
        )
        
        print(f"[{request_id}] Got response from Ollama: status {response.status_code}")
        
        # Create a streaming response
        def generate():
            for chunk in response.iter_content(chunk_size=4096):
                yield chunk
                
        # Return a streaming response
        return Response(
            generate(),
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
        
    except Exception as e:
        print(f"Error in enhanced_request: {str(e)}")
        print(traceback.format_exc())
        # Fall back to direct proxy if anything goes wrong
        return direct_proxy(f"{OLLAMA_API}/{endpoint}", original_request)

def direct_proxy(target_url, original_request):
    """Forward the request directly to Ollama without modification"""
    print(f"Proxying request to: {target_url} (Method: {original_request.method})")
    
    try:
        # Extract and print request data for debugging (limited to avoid large logs)
        if original_request.data:
            try:
                data_str = original_request.data.decode('utf-8')
                if len(data_str) > 200:
                    print(f"Request data: {data_str[:200]}... (truncated)")
                else:
                    print(f"Request data: {data_str}")
            except:
                print(f"Request data: (binary data, not shown)")
        
        # Forward the request to Ollama
        response = requests.request(
            method=original_request.method,
            url=target_url,
            headers={key: value for key, value in original_request.headers if key != 'Host'},
            data=original_request.get_data(),
            cookies=original_request.cookies,
            allow_redirects=False,
            stream=True  # Always stream the response
        )
        
        print(f"Response from {target_url}: status {response.status_code}")
        
        # Create a streaming response
        def generate():
            for chunk in response.iter_content(chunk_size=4096):
                yield chunk
                
        # Return a streaming response
        return Response(
            generate(),
            status=response.status_code,
            headers=dict(response.headers)
        )
    except Exception as e:
        print(f"Error in direct_proxy: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/status', methods=['GET'])
def status():
    """Check the status of the proxy and its connections"""
    status_info = {
        "proxy": "online",
        "timestamp": datetime.now().isoformat()
    }
    
    # Check Neo4j connection
    if searcher and searcher.driver:
        try:
            with searcher.driver.session() as session:
                result = session.run("RETURN 'Connected!' as message")
                neo4j_message = result.single()["message"]
                status_info["neo4j"] = {
                    "status": "connected",
                    "message": neo4j_message
                }
        except Exception as e:
            status_info["neo4j"] = {
                "status": "error",
                "error": str(e)
            }
    else:
        status_info["neo4j"] = {
            "status": "error",
            "error": "'NoneType' object has no attribute 'session'"
        }
    
    # Check Ollama connection
    try:
        response = requests.get(f"{OLLAMA_API}/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            status_info["ollama"] = {
                "status": "connected",
                "models": len(models)
            }
        else:
            status_info["ollama"] = {
                "status": "error",
                "status_code": response.status_code
            }
    except Exception as e:
        status_info["ollama"] = {
            "status": "error",
            "error": str(e)
        }
    
    return jsonify(status_info)

@app.route('/')
def index():
    """Serve the index page"""
    return """
    <html>
    <head>
        <title>Ollama Proxy with Knowledge Graph</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            h1 { color: #333; }
            h2 { color: #555; }
            a { color: #0066cc; text-decoration: none; }
            a:hover { text-decoration: underline; }
            .nav { display: flex; gap: 20px; margin: 20px 0; }
            .card { border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin-bottom: 15px; }
        </style>
    </head>
    <body>
        <h1>Ollama Proxy with Knowledge Graph</h1>
        <p>This proxy enhances Ollama requests with context from your knowledge graph.</p>
        
        <div class="nav">
            <a href="/status">Status</a>
            <a href="/models">Model Management</a>
        </div>
        
        <div class="card">
            <h2>Use with OpenWebUI</h2>
            <p>OpenWebUI is configured to use this proxy at: <code>http://ollama-proxy:11435</code></p>
        </div>
        
        <div class="card">
            <h2>Endpoints</h2>
            <ul>
                <li><code>/api/...</code> - Proxies requests to Ollama, enhancing chat/generate requests</li>
                <li><code>/status</code> - Shows the connection status of components</li>
                <li><code>/models</code> - Manage Ollama models</li>
            </ul>
        </div>
    </body>
    </html>
    """

@app.route('/models')
def models_page():
    """Serve the models management page"""
    return app.send_static_file('models.html')

if __name__ == '__main__':
    # Add the static directory if it doesn't exist
    os.makedirs('static', exist_ok=True)
    
    # Create the models.html file if it doesn't exist
    models_html_path = os.path.join('static', 'models.html')
    if not os.path.exists(models_html_path):
        with open(models_html_path, 'w') as f:
            f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Ollama Model Management</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        button { padding: 8px 15px; margin: 5px; cursor: pointer; }
        .model-list { margin-top: 20px; }
        .model { border: 1px solid #ddd; padding: 10px; margin-bottom: 10px; border-radius: 5px; }
        .status { color: green; }
        .error { color: red; }
    </style>
</head>
<body>
    <h1>Ollama Model Management</h1>
    <div>
        <h2>Load Model</h2>
        <input type="text" id="model-name" placeholder="Model name (e.g., llama3.1)">
        <button onclick="loadModel()">Load Model</button>
    </div>
    
    <div class="model-list">
        <h2>Available Models</h2>
        <button onclick="listModels()">Refresh List</button>
        <div id="models"></div>
    </div>
    
    <div id="status" class="status"></div>
    
    <script>
        function loadModel() {
            const modelName = document.getElementById('model-name').value;
            if (!modelName) {
                setStatus('Please enter a model name', true);
                return;
            }
            
            setStatus('Loading model ' + modelName + '...');
            
            fetch('/api/pull', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name: modelName })
            })
            .then(response => response.json())
            .then(data => {
                setStatus('Model ' + modelName + ' loaded successfully');
                listModels();
            })
            .catch(error => {
                setStatus('Error loading model: ' + error, true);
            });
        }
        
        function listModels() {
            setStatus('Fetching models...');
            
            fetch('/api/tags')
            .then(response => response.json())
            .then(data => {
                const modelsDiv = document.getElementById('models');
                modelsDiv.innerHTML = '';
                
                if (data.models && data.models.length > 0) {
                    data.models.forEach(model => {
                        const modelDiv = document.createElement('div');
                        modelDiv.className = 'model';
                        modelDiv.innerHTML = `
                            <h3>${model.name}</h3>
                            <p>Size: ${formatSize(model.size)}</p>
                            <p>Modified: ${new Date(model.modified).toLocaleString()}</p>
                        `;
                        modelsDiv.appendChild(modelDiv);
                    });
                    setStatus('Found ' + data.models.length + ' models');
                } else {
                    modelsDiv.innerHTML = '<p>No models found</p>';
                    setStatus('No models found');
                }
            })
            .catch(error => {
                setStatus('Error fetching models: ' + error, true);
            });
        }
        
        function formatSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
            if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
            return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
        }
        
        function setStatus(message, isError = false) {
            const statusDiv = document.getElementById('status');
            statusDiv.textContent = message;
            statusDiv.className = isError ? 'error' : 'status';
        }
        
        // Load models on page load
        document.addEventListener('DOMContentLoaded', listModels);
    </script>
</body>
</html>""")
    
    # Run the application
    app.run(host='0.0.0.0', port=11435, debug=True)
