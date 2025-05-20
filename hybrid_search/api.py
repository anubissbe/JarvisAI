from flask import Flask, request, jsonify
from hybrid_search import HybridSearch
import requests

app = Flask(__name__)

# Use the correct password we've confirmed works
searcher = HybridSearch(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="VerySecurePassword",
    milvus_host="localhost",
    milvus_port="19530",
    ollama_url="http://localhost:11434"
)

@app.route('/')
def index():
    return app.send_static_file('index.html')

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
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

# Add to api.py
conversations = {}

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    query = data.get('query')
    user_id = data.get('user_id', 'default')

    # Initialize conversation if needed
    if user_id not in conversations:
        conversations[user_id] = []

    # Search for relevant documents
    search_results = searcher.hybrid_search(
        query_text=query,
        knowledge_base_id="96c3b9a4-10c1-400c-9d22-3e71cb8ed7fb",
        top_k=3
    )

    # Format context from search results
    context_pieces = []
    for r in search_results:
        context = f"Document: {r.get('title', 'Unknown')}\n"

        if "concept" in r and "concept_description" in r:
            context += f"Concept: {r['concept']} - {r['concept_description']}\n"

        if "content" in r:
            context += r.get('content', '')

        context_pieces.append(context)

    context = "\n\n".join(context_pieces)

    # Call Ollama with context
    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": "llama3.1",
            "messages": [
                {"role": "system", "content": "You are Jarvis, a helpful AI assistant. Use the provided document information to answer the user's question accurately."},
                *conversations[user_id],
                {"role": "user", "content": query}
            ],
            "options": {
                "temperature": 0.7,
                "system": f"Use the following information to help answer the user's question:\n\n{context}"
            }
        }
    ).json()

    # Extract assistant response
    assistant_message = response.get("message", {}).get("content", "Sorry, I couldn't generate a response.")

    # Update conversation history
    conversations[user_id].append({"role": "user", "content": query})
    conversations[user_id].append({"role": "assistant", "content": assistant_message})

    # Keep conversation history limited to last 10 messages
    if len(conversations[user_id]) > 10:
        conversations[user_id] = conversations[user_id][-10:]

    return jsonify({
        "response": assistant_message,
        "context": context_pieces,
        "sources": [r.get("title") for r in search_results]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

