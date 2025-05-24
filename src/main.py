from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
import uvicorn
import os
import logging
import time
from datetime import datetime

from core.jarvis import JarvisAI
from core.websocket import JarvisWebSocket
from language.detector import LanguageDetector
from knowledge.manager import KnowledgeManager
from memory.manager import MemoryManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.getenv('LOG_DIR', '/app/logs'), 'jarvis.log'))
    ]
)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize API key security
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Initialize components as None
jarvis = None
knowledge_manager = None
websocket_server = None

async def verify_api_key(api_key: str = Depends(api_key_header)):
    """Verify API key if enabled"""
    if os.getenv('REQUIRE_API_KEY', 'false').lower() == 'true':
        if not api_key or api_key != os.getenv('API_KEY'):
            raise HTTPException(
                status_code=401,
                detail="Invalid or missing API key"
            )
    return api_key

async def get_memory_manager() -> MemoryManager:
    """Get the initialized memory manager instance"""
    if not jarvis or not jarvis.memory_manager:
        raise HTTPException(
            status_code=503,
            detail="Memory manager not initialized"
        )
    return jarvis.memory_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize components
    global jarvis, knowledge_manager, websocket_server
    
    try:
        # Create required directories
        os.makedirs(os.getenv('LOG_DIR', '/app/logs'), exist_ok=True)
        
        # Initialize KnowledgeManager first (this has built-in retry logic)
        knowledge_manager = KnowledgeManager()
        
        # Initialize Memory Manager with cleanup configuration
        memory_manager = MemoryManager(
            retention_days=int(os.getenv('MEMORY_RETENTION_DAYS', '365')),
            archive_days=int(os.getenv('MEMORY_ARCHIVE_DAYS', '730')),
            max_conversation_history=int(os.getenv('MAX_CONVERSATION_HISTORY', '1000'))
        )
        
        # Initialize Jarvis with all components
        jarvis = JarvisAI(
            knowledge_manager=knowledge_manager,
            memory_manager=memory_manager,
            language_detector=LanguageDetector()
        )
        
        # Initialize WebSocket server
        websocket_server = JarvisWebSocket(
            app=app,
            memory_manager=memory_manager,
            knowledge_manager=knowledge_manager
        )
        
        logger.info("All components initialized successfully")
        yield
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise
    finally:
        # Cleanup code
        try:
            if memory_manager:
                await memory_manager.cleanup_old_conversations()
            if websocket_server:
                await websocket_server.cleanup_background_tasks()
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
        logger.info("Shutting down")

app = FastAPI(
    title="Jarvis AI Backend",
    description="Advanced bilingual AI assistant API",
    version="3.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv('ALLOWED_ORIGINS', '*').split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add rate limiter error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4096)
    conversation_id: Optional[str] = Field(None, max_length=64)
    context: Optional[Dict[str, Any]] = None

    @validator('message')
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError('Message cannot be empty or just whitespace')
        return v.strip()

class ChatResponse(BaseModel):
    response: str
    language: str
    sources: Optional[list] = None
    conversation_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    status = {
        "status": "healthy",
        "components": {
            "jarvis": "healthy" if jarvis else "not_initialized",
            "knowledge_manager": "healthy" if knowledge_manager else "not_initialized",
            "websocket": "healthy" if websocket_server else "not_initialized"
        },
        "metrics": {
            "active_connections": len(websocket_server.connection_manager.active_connections) if websocket_server else 0,
            "total_memory_entries": await jarvis.memory_manager.get_total_entries() if jarvis else 0
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Check component health
    try:
        if knowledge_manager:
            await knowledge_manager.health_check()
        
        if websocket_server:
            active_connections = len(websocket_server.connection_manager.active_connections)
            if active_connections > 0:
                status["components"]["websocket"] = f"healthy ({active_connections} active connections)"
    except Exception as e:
        logger.error(f"Health check error: {str(e)}", exc_info=True)
        status["components"]["knowledge_manager"] = f"unhealthy: {str(e)}"
        status["status"] = "degraded"
    
    return status

@app.post("/chat", response_model=ChatResponse)
@limiter.limit(os.getenv('RATE_LIMIT', '60/minute'))
async def chat(
    request: ChatRequest,
    api_key: str = Depends(verify_api_key)
):
    """Process a chat message"""
    if not jarvis:
        raise HTTPException(
            status_code=503,
            detail="Jarvis AI is initializing, please try again in a moment"
        )
    
    try:
        start_time = time.time()
        response = await jarvis.process_message(
            message=request.message,
            conversation_id=request.conversation_id,
            context=request.context
        )
        
        # Log processing time
        processing_time = time.time() - start_time
        logger.info(f"Message processed in {processing_time:.2f} seconds")
        
        return {
            **response,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@app.post("/upload-knowledge")
@limiter.limit(os.getenv('UPLOAD_RATE_LIMIT', '10/minute'))
async def upload_knowledge(
    file: Any,  # This will be properly typed when implementing file handling
    api_key: str = Depends(verify_api_key)
):
    """Upload a document to the knowledge base"""
    if not knowledge_manager:
        raise HTTPException(
            status_code=503,
            detail="Knowledge manager is initializing, please try again in a moment"
        )
    
    try:
        # Validate file size
        max_size = int(os.getenv('MAX_UPLOAD_SIZE_MB', '10')) * 1024 * 1024  # Convert to bytes
        if hasattr(file, 'size') and file.size > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds maximum limit of {max_size // (1024 * 1024)}MB"
            )
        
        start_time = time.time()
        result = await knowledge_manager.add_document(file)
        
        # Log processing time
        processing_time = time.time() - start_time
        logger.info(f"Document processed in {processing_time:.2f} seconds")
        
        return {
            "status": "success",
            "message": f"Document added: {result}",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error uploading knowledge: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to upload document",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@app.delete("/conversation/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Delete a conversation and its associated memory"""
    try:
        await jarvis.memory_manager.forget_conversation(conversation_id)
        return {
            "status": "success",
            "message": f"Conversation {conversation_id} deleted",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error deleting conversation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to delete conversation",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@app.get("/metrics/websocket")
async def websocket_metrics(api_key: str = Depends(verify_api_key)):
    """Get WebSocket connection metrics"""
    if not websocket_server:
        raise HTTPException(
            status_code=503,
            detail="WebSocket server not initialized"
        )
    
    try:
        active_connections = websocket_server.connection_manager.active_connections
        connection_metadata = websocket_server.connection_manager.connection_metadata
        
        metrics = {
            "active_connections": len(active_connections),
            "connections": [
                {
                    "id": conn_id,
                    "connected_at": metadata["connected_at"],
                    "last_active": metadata["last_active"],
                    "messages_received": metadata["messages_received"],
                    "messages_sent": metadata["messages_sent"]
                }
                for conn_id, metadata in connection_metadata.items()
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return metrics
    except Exception as e:
        logger.error(f"Error getting WebSocket metrics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to get WebSocket metrics",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv('PORT', '5000')),
        reload=os.getenv('DEBUG', 'false').lower() == 'true',
        log_level=os.getenv('LOG_LEVEL', 'info').lower(),
        workers=int(os.getenv('WORKERS', '1'))
    )