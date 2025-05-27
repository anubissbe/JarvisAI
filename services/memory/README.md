# JarvisAI Memory Service

This service implements the dual memory architecture for JarvisAI, providing access to:

- Global knowledge base (shared across all users)
- User-specific memories (private per user)
- Temporal memory layers with automatic promotion

## API Endpoints

- `GET /memory/global` - Search global knowledge
- `GET /memory/user/{user_id}` - Get user-specific memories
- `POST /memory/store` - Store new memories
- `POST /memory/promote` - Manually promote memories

## Memory Storage

- Weaviate: Vector database for semantic search (100GB)
- ArangoDB: Graph database for relationships (50GB)
- ChromaDB: Vector database for recent memories (25GB)
- Redis: Cache for session memories (10GB)

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn main:app --reload
```