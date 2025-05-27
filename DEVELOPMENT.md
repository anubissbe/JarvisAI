# JarvisAI-0.1 Development Guide

## Development Environment Setup

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- NVIDIA GPU with CUDA support
- IDE with Python support (VS Code recommended)
- Git

### Local Development Setup

1. **Clone the Repository**
```bash
git clone https://github.com/your-org/jarvisai-0.1
cd jarvisai-0.1
```

2. **Create Python Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/MacOS
.\venv\Scripts\activate   # Windows
```

3. **Install Development Dependencies**
```bash
# Install core dependencies
pip install -r services/memory/requirements.txt
pip install -r services/learning/requirements.txt
pip install -r services/documents/requirements.txt

# Install development tools
pip install black ruff mypy pytest pytest-cov pre-commit
```

4. **Set Up Pre-commit Hooks**
```bash
pre-commit install
```

### Development Workflow

1. **Branch Naming Convention**
```
feature/descriptive-name    # For new features
fix/issue-description      # For bug fixes
docs/what-changed         # For documentation
refactor/what-changed    # For code refactoring
```

2. **Running Services Locally**

Memory Service:
```bash
cd services/memory
uvicorn main:app --reload --port 8000
```

Learning Service:
```bash
cd services/learning
uvicorn main:app --reload --port 8001
```

Document Service:
```bash
cd services/documents
uvicorn main:app --reload --port 8002
```

3. **Running Tests**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=jarvisai tests/

# Run specific test file
pytest tests/test_memory.py
```

4. **Code Quality**
```bash
# Format code
black .

# Lint code
ruff check .

# Type checking
mypy .
```

### Docker Development

1. **Building Services**
```bash
# Build all services
docker-compose build

# Build specific service
docker-compose build memory-service
```

2. **Running Services**
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Start specific service
docker-compose up -d memory-service
```

3. **Debugging in Docker**
```bash
# Attach to container
docker exec -it jarvisai-webui /bin/bash

# View logs
docker-compose logs memory-service
```

### API Development

1. **FastAPI Development**
- Use Pydantic models for request/response validation
- Document all endpoints with docstrings
- Include example requests in docstrings
- Add appropriate tags for API grouping

Example:
```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class Memory(BaseModel):
    content: str
    category: str
    user_id: str

@router.post("/memory/store", tags=["memory"])
async def store_memory(memory: Memory):
    """
    Store a new memory.
    
    Example:
        {
            "content": "User prefers dark mode",
            "category": "preference",
            "user_id": "user123"
        }
    """
    try:
        # Implementation
        pass
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

2. **Error Handling**
- Use custom exception classes
- Provide meaningful error messages
- Include error codes for frontend handling

### Memory System Development

1. **Memory Types**
- Global Knowledge (shared across users)
- User Memories (private per user)
- Session Memories (temporary)
- Temporal Memories (with promotion)

2. **Database Interactions**
- Use connection pooling
- Implement retry mechanisms
- Handle transaction rollbacks
- Cache frequently accessed data

Example:
```python
from typing import Optional
from contextlib import contextmanager

class MemoryStore:
    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = self.pool.get_connection()
            yield conn
        finally:
            if conn:
                self.pool.return_connection(conn)

    async def store_memory(self, memory: Memory) -> Optional[str]:
        with self.get_connection() as conn:
            try:
                memory_id = await conn.store(memory)
                return memory_id
            except Exception as e:
                logger.error(f"Failed to store memory: {e}")
                return None
```

### Plugin Development

1. **Plugin Structure**
```
plugins/
├── weather/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   └── README.md
└── news/
    ├── __init__.py
    ├── main.py
    ├── config.py
    └── README.md
```

2. **Plugin Interface**
```python
from abc import ABC, abstractmethod
from typing import Any, Dict

class PluginInterface(ABC):
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize plugin resources"""
        pass
    
    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute plugin functionality"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup plugin resources"""
        pass
```

### Documentation Guidelines

1. **Code Documentation**
- Use descriptive variable and function names
- Add docstrings to all functions and classes
- Include type hints
- Document exceptions and edge cases

2. **API Documentation**
- Use OpenAPI/Swagger annotations
- Provide example requests and responses
- Document error conditions
- Include authentication requirements

3. **README Updates**
- Keep installation instructions up to date
- Document new features and changes
- Update configuration examples
- Add troubleshooting guides

### Commit Guidelines

1. **Commit Message Format**
```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation
- style: Formatting
- refactor: Code restructuring
- test: Adding tests
- chore: Maintenance

Example:
```
feat(memory): implement temporal memory promotion

- Add promotion criteria checking
- Implement promotion workflow
- Add tests for promotion logic

Closes #123
```

2. **Pull Request Process**
- Create feature branch
- Update documentation
- Add/update tests
- Run code quality checks
- Create detailed PR description
- Request review from team members

### Troubleshooting Development Issues

1. **Docker Issues**
```bash
# Remove all containers and volumes
docker-compose down -v

# Rebuild everything
docker-compose build --no-cache
```

2. **Database Issues**
```bash
# Reset memory systems
python -m jarvisai.memory.init_memory --force

# Clear Redis cache
docker exec jarvisai-redis redis-cli FLUSHALL
```

3. **Common Problems**
- Check Docker logs for errors
- Verify environment variables
- Ensure GPU drivers are working
- Check database connections
- Verify model downloads

### Performance Optimization

1. **Memory Usage**
- Use connection pooling
- Implement caching strategies
- Close connections properly
- Monitor memory leaks

2. **Response Time**
- Optimize database queries
- Use async/await properly
- Implement request batching
- Cache frequent operations

3. **Resource Management**
- Monitor GPU usage
- Track database size
- Watch memory consumption
- Log performance metrics