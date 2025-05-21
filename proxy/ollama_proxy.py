from flask import Flask, request, jsonify, Response, stream_with_context
import logging
import os
import requests
import sys

# Ensure the shared hybrid_search module can be located
sys.path.append("/opt/jarvis")
from hybrid_search import HybridSearch

app = Flask(__name__)

# Configure logging
log_level = os.environ.get("LOG_LEVEL", "info").upper()
logging.basicConfig(level=getattr(logging, log_level, logging.INFO))
logger = logging.getLogger("ollama_proxy")

# Connection details from environment variables
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")
if not NEO4J_PASSWORD:
    raise RuntimeError("NEO4J_PASSWORD environment variable not set or empty")
MILVUS_HOST = os.environ.get("MILVUS_HOST", "milvus-standalone")
MILVUS_PORT = os.environ.get("MILVUS_PORT", "19530")
OLLAMA_API_BASE_URL = os.environ.get("OLLAMA_API_BASE_URL", "http://ollama:11434")
OPENWEBUI_API_BASE_URL = os.environ.get("OPENWEBUI_API_BASE_URL", "http://open-webui:8080")

try:
    hybrid_search = HybridSearch(
        neo4j_uri=NEO4J_URI,
        neo4j_user=NEO4J_USER,
        neo4j_password=NEO4J_PASSWORD,
        milvus_host=MILVUS_HOST,
        milvus_port=MILVUS_PORT,
        ollama_url=OLLAMA_API_BASE_URL,
        openwebui_url=OPENWEBUI_API_BASE_URL,
    )
except Exception as exc:
    logger.error("Failed to initialise HybridSearch: %s", exc)
    hybrid_search = None

@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(path):
    logger.info("Received request for /api/%s (Method: %s)", path, request.method)

    data = request.get_json(silent=True)

    # For chat requests, augment with hybrid search context
    if path == 'chat' and data is not None and hybrid_search is not None:
        logger.info("Processing chat request via hybrid search")

        # Extract latest user message
        user_message = ""
        messages = data.get("messages", [])
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break

        kb_id = (
            data.get("knowledge_base_id")
            or data.get("kb_id")
            or data.get("knowledge_id")
            or os.environ.get("DEFAULT_KB_ID")
        )

        if user_message and kb_id:
            try:
                results = hybrid_search.hybrid_search(user_message, kb_id, top_k=3)
                context_parts = [r.get("content", "") for r in results if r.get("content")]
                if context_parts:
                    options = data.setdefault("options", {})
                    existing = options.get("system", "")
                    context = "\n\n".join(context_parts)
                    options["system"] = f"{existing}\n\nContext:\n{context}".strip()
                    logger.info("Added %d context snippets to system prompt", len(context_parts))
            except Exception as exc:
                logger.error("Hybrid search failed: %s", exc)
    else:
        if path == 'chat' and data is not None:
            logger.warning("Hybrid search is not available, proceeding without knowledge augmentation")

    # Pass through to Ollama for all requests
    url = f"{OLLAMA_API_BASE_URL}/api/{path}"
    logger.info("Proxying request to: %s (Method: %s)", url, request.method)

    headers = {k: v for k, v in request.headers if k.lower() != 'host'}
    try:
        timeout = int(os.environ.get("REQUEST_TIMEOUT", "300"))
        resp = requests.request(
            method=request.method,
            url=url,
            params=request.args,
            json=data,
            headers=headers,
            stream=True,
            timeout=timeout,
        )
    except requests.RequestException as exc:
        logger.error("Request to Ollama failed: %s", exc)
        return jsonify({"error": "Failed to contact Ollama"}), 502

    logger.info("Response from %s: status %s", url, resp.status_code)

    return Response(
        stream_with_context(resp.iter_content(chunk_size=8192)),
        status=resp.status_code,
        headers=dict(resp.headers),
    )

if __name__ == '__main__':
    # Run on the same port exposed by the Docker container
    app.run(host='0.0.0.0', port=11435)
