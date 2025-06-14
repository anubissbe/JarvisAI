# JarvisAI Backend

FastAPI-based backend for the JarvisAI self-hosted AI assistant.

## Features Implemented

### ✅ Authentication System
- JWT-based authentication with access and refresh tokens
- User registration and login
- OAuth2 support (Google and GitHub)
- Role-based access control (RBAC)
- Password hashing with bcrypt
- Token validation middleware

### 🔄 In Progress
- Chat API endpoints
- Model management
- Document processing
- Agent orchestration

## Quick Start

### 1. Prerequisites
- Python 3.11+
- Docker and Docker Compose
- PostgreSQL (via Docker)
- Redis (via Docker)

### 2. Setup Development Environment

```bash
# Clone the repository
cd backend/

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start infrastructure services
docker-compose -f ../docker-compose.dev.yml up -d

# Copy environment variables
cp .env.example .env
# Edit .env with your configuration
```

### 3. Run the Application

```bash
# Development mode with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or use the Python script
python main.py
```

### 4. Access the Application

- API Documentation: http://localhost:8000/docs
- Alternative API Docs: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login (OAuth2 compatible)
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout current user
- `GET /api/v1/auth/me` - Get current user info
- `GET /api/v1/auth/oauth/{provider}` - Initiate OAuth flow
- `GET /api/v1/auth/callback/{provider}` - OAuth callback

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py
```

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── auth.py       # Authentication endpoints
│   │   │   │   └── ...
│   │   │   └── router.py         # Main API router
│   │   └── deps.py               # API dependencies
│   ├── core/
│   │   ├── config.py             # Settings management
│   │   ├── database.py           # Database configuration
│   │   ├── exceptions.py         # Custom exceptions
│   │   ├── logging.py            # Logging setup
│   │   └── security.py           # Security utilities
│   ├── middleware/
│   │   ├── auth.py               # Authentication middleware
│   │   └── security.py           # Security headers
│   └── models/
│       └── user.py               # User models and schemas
├── tests/
│   └── test_auth.py              # Authentication tests
├── main.py                       # Application entry point
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
└── Dockerfile                    # Container configuration
```

## Security Features

- **JWT Tokens**: Secure token-based authentication
- **Password Hashing**: Bcrypt with salt
- **CORS**: Configurable CORS middleware
- **Rate Limiting**: Built-in rate limiting support
- **Security Headers**: Security middleware for headers
- **Input Validation**: Pydantic models for all inputs

## Environment Variables

Key environment variables (see `.env.example` for full list):

- `SECRET_KEY`: JWT signing key (generate a strong one!)
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `DEBUG`: Enable debug mode
- `CORS_ORIGINS`: Allowed CORS origins

## Next Steps

1. **Complete API Endpoints**:
   - Chat functionality
   - Model management
   - Document processing
   - Agent orchestration

2. **Add Database Migrations**:
   - Set up Alembic
   - Create initial migrations

3. **Implement Business Logic**:
   - Ollama integration
   - RAG pipeline
   - Multi-agent orchestration

4. **Add Monitoring**:
   - Prometheus metrics
   - Structured logging
   - Error tracking

## Contributing

1. Follow the existing code style
2. Add tests for new features
3. Update documentation
4. Run linting and tests before committing

## License

See the main project LICENSE file.