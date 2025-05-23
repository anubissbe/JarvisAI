"""
Main entry point for Jarvis AI Assistant.

This module initializes and runs the Jarvis system, providing both
a command-line interface and a REST API for interacting with the assistant.
"""

import argparse
import logging
import os
import sys
import signal
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
import threading
import uvicorn
from fastapi import FastAPI, Request, HTTPException, Depends, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from core import JarvisEngine
from utilities.auth import get_api_key, get_admin_api_key

# Initialize rate limiter with default limits
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

# Initialize FastAPI with rate limiter
app = FastAPI(
    title="Jarvis AI API",
    description="API for Jarvis AI Assistant",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add global rate limiting
@app.middleware("http")
async def global_rate_limit(request: Request, call_next):
    try:
        await limiter.check(request)
        response = await call_next(request)
        return response
    except RateLimitExceeded:
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded. Please try again later."}
        )

# Allow CORS with production-ready secure configuration
def get_allowed_origins():
    """Get allowed origins from environment or use defaults."""
    # In production, get from environment variable (comma-separated)
    origins_env = os.environ.get("ALLOWED_ORIGINS", None)
    if origins_env:
        return [origin.strip() for origin in origins_env.split(",")]
    
    # Default development origins if not specified
    return [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080", 
        "http://127.0.0.1:8080"
    ]

# Add CORS middleware with secure configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # Restrict to needed methods
    allow_headers=["Content-Type", "Authorization", "Accept"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Global Jarvis instance
jarvis_instance = None


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str
    history: Optional[list] = None
    force_web_search: Optional[bool] = False


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str
    language: str
    sources: Optional[List[str]] = None


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Jarvis AI API is running"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    # Check core system components
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "api": {"status": "healthy"},
            "llm": {"status": "unknown"},
            "vector_db": {"status": "unknown"}
        },
        "version": "0.1.0"
    }
    
    # Check LLM connection
    global jarvis_instance
    if jarvis_instance and jarvis_instance.llm:
        try:
            models = jarvis_instance.llm.get_available_models()
            health_status["components"]["llm"] = {
                "status": "healthy" if models else "degraded",
                "models": models
            }
        except Exception as e:
            health_status["components"]["llm"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
    
    # Check vector DB connection
    if jarvis_instance and jarvis_instance.knowledge and jarvis_instance.knowledge.collection:
        try:
            # Just try to get collection info
            collection_name = jarvis_instance.knowledge.collection.name
            health_status["components"]["vector_db"] = {
                "status": "healthy",
                "collection": collection_name
            }
        except Exception as e:
            health_status["components"]["vector_db"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
    
    # If any component is unhealthy, mark overall status as degraded
    if any(comp["status"] == "unhealthy" for comp in health_status["components"].values()):
        health_status["status"] = "degraded"
    
    return health_status

@app.get("/metrics", response_model=Dict[str, Any])
async def metrics(api_key: dict = Depends(get_admin_api_key)):
    """Metrics endpoint for monitoring."""
    global jarvis_instance
    if not jarvis_instance:
        raise HTTPException(
            status_code=500,
            detail="Jarvis is not initialized"
        )
    
    try:
        # Collect system metrics
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "api": {
                "uptime_seconds": time.time() - jarvis_instance.start_time,
                "request_count": jarvis_instance.request_count,
                "error_count": jarvis_instance.error_count,
                "last_error": jarvis_instance.last_error,
                "success_rate": (
                    ((jarvis_instance.request_count - jarvis_instance.error_count) / 
                     jarvis_instance.request_count * 100) if jarvis_instance.request_count > 0 else 100
                )
            },
            "memory": {
                "conversation_context_size": len(jarvis_instance.memory.current_context),
                "verified_facts_count": len(jarvis_instance.knowledge.verified_facts) if hasattr(jarvis_instance.knowledge, "verified_facts") else 0
            }
        }
        
        # Add LLM metrics
        if jarvis_instance.llm:
            try:
                metrics["llm"] = {
                    "status": "healthy",
                    "model": jarvis_instance.llm.model,
                    "available_models": jarvis_instance.llm.get_available_models()
                }
            except Exception as e:
                metrics["llm"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        # Add vector DB metrics
        if jarvis_instance.knowledge and jarvis_instance.knowledge.collection:
            try:
                metrics["vector_db"] = {
                    "status": "healthy",
                    "collection_name": jarvis_instance.knowledge.collection.name,
                    "collection_count": jarvis_instance.knowledge.collection.count()
                }
            except Exception as e:
                metrics["vector_db"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error collecting metrics: {str(e)}"
        )


# Create a standard error response model
class ErrorResponse(BaseModel):
    """Standard error response model."""
    success: bool = False
    error: str
    details: Optional[str] = None

@app.post("/chat", response_model=ChatResponse, responses={500: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
@limiter.limit("10/minute")
async def chat(request: ChatRequest, request_obj: Request = None, api_key: dict = Depends(get_api_key)):
    """Chat endpoint."""
    global jarvis_instance
    if not jarvis_instance:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Jarvis is not initialized"}
        )
    
    # Process the user input
    response = jarvis_instance.process_input(request.message, force_web_search=request.force_web_search)
    
    # Detect language of the user message
    language = jarvis_instance.language.detect_language(request.message)
    
    # Get sources if available from the last interaction
    sources = []
    if jarvis_instance.memory.current_context:
        last_interaction = jarvis_instance.memory.current_context[-1]
        if "knowledge_info" in last_interaction and last_interaction["knowledge_info"]:
            sources = last_interaction["knowledge_info"].get("sources", [])
    
    return ChatResponse(response=response, language=language, sources=sources)


class WebSearchRequest(BaseModel):
    """Request model for web search endpoint."""
    query: str
    language: Optional[str] = "en"


class WebSearchResponse(BaseModel):
    """Response model for web search endpoint."""
    results: List[Dict[str, Any]]


@app.post("/web-search", response_model=WebSearchResponse, responses={
    500: {"model": ErrorResponse},
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    429: {"model": ErrorResponse}
})
@limiter.limit("5/minute")
async def web_search(
    request: WebSearchRequest,
    request_obj: Request = None,
    api_key: dict = Depends(get_api_key)
):
    """Web search endpoint."""
    global jarvis_instance
    if not jarvis_instance:
        raise HTTPException(
            status_code=500,
            detail="Jarvis is not initialized"
        )
    
    try:
        # Detect language if not specified
        language = request.language
        if not language:
            language = jarvis_instance.language.detect_language(request.query)
        
        # Validate query length
        if len(request.query.strip()) < 3:
            raise HTTPException(
                status_code=400,
                detail="Search query must be at least 3 characters long"
            )
        
        # Perform web search with timeout
        results = await asyncio.wait_for(
            jarvis_instance.direct_web_search(request.query, language),
            timeout=10.0  # 10 second timeout
        )
        
        if not results:
            return WebSearchResponse(
                results=[],
                message="No results found"
            )
        
        return WebSearchResponse(results=results)
        
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Web search timed out"
        )
    except Exception as e:
        logging.error(f"Web search error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error performing web search: {str(e)}"
        )


class KnowledgeAddRequest(BaseModel):
    """Request model for adding knowledge."""
    content: str
    source: Optional[str] = "User Input"
    language: Optional[str] = None
    domain: Optional[str] = None
    tags: Optional[List[str]] = None


class KnowledgeAddResponse(BaseModel):
    """Response model for adding knowledge."""
    success: bool
    message: str


@app.post("/knowledge/add", response_model=KnowledgeAddResponse, responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def add_knowledge(request: KnowledgeAddRequest, api_key: dict = Depends(get_api_key)):
    """Add information to the knowledge base."""
    global jarvis_instance
    if not jarvis_instance:
        return {"success": False, "message": "Jarvis is not initialized"}
    
    # Prepare metadata
    metadata = {
        "source": request.source,
        "domain": request.domain or "user_knowledge"
    }
    
    if request.language:
        metadata["language"] = request.language
    
    if request.tags:
        metadata["tags"] = request.tags
    
    # Add to knowledge base
    success = jarvis_instance.add_to_knowledge_base(request.content, metadata)
    
    if success:
        return {"success": True, "message": "Knowledge successfully added to the database"}
    else:
        return {"success": False, "message": "Failed to add knowledge to the database"}


class ConversationHistoryResponse(BaseModel):
    """Response model for conversation history."""
    history: str


@app.get("/conversation/history", response_model=ConversationHistoryResponse)
async def get_conversation_history(max_interactions: int = 10):
    """Get a summary of recent conversations."""
    global jarvis_instance
    if not jarvis_instance:
        return {"history": "Jarvis is not initialized"}
    
    history = jarvis_instance.get_conversation_summary(max_interactions)
    return {"history": history}


@app.post("/conversation/clear")
async def clear_conversation():
    """Clear the current conversation context."""
    global jarvis_instance
    if not jarvis_instance:
        return {"success": False, "message": "Jarvis is not initialized"}
    
    jarvis_instance.memory.clear_conversation_context()
    return {"success": True, "message": "Conversation context cleared"}


def setup_logging(log_level: str = "INFO") -> None:
    """Set up logging configuration.
    
    Args:
        log_level: The logging level to use.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    logs_dir = os.path.expanduser("~/.jarvis/logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Set up rotating file handler for better log management
    from logging.handlers import RotatingFileHandler
    
    # Main log file with rotation (10MB max size, keep 10 backup files)
    main_log_file = os.path.join(logs_dir, "jarvis.log")
    main_handler = RotatingFileHandler(
        main_log_file, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    
    # Error log file with rotation
    error_log_file = os.path.join(logs_dir, "errors.log")
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    # Only log errors and above to this handler
    error_handler.setLevel(logging.ERROR)
    
    # Configure formats
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    main_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)
    
    # Add stream handler for console output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove any existing handlers to avoid duplicates on reload
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add all handlers
    root_logger.addHandler(main_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(console_handler)
    
    # Reduce verbosity of some third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from a file.
    
    Args:
        config_path: Optional path to a configuration file.
        
    Returns:
        A dictionary with the configuration.
    """
    import json
    
    # Default configuration
    default_config = {
        "log_level": "INFO",
        "memory_dir": os.path.expanduser("~/.jarvis/memory"),
        "knowledge_dir": os.path.expanduser("~/.jarvis/knowledge"),
        "max_context_size": 10,
        "enable_web_search": True,
        "api_host": "0.0.0.0",
        "api_port": 8000,
        "enable_api": True,
        "enable_cli": True,
        "chroma_url": "http://chroma-db:8000",
        "ollama_url": "http://ollama:11434"
    }
    
    # If no config path is provided, use default
    if not config_path:
        return default_config
    
    # Try to load config from file
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
        
        # Validate config values
        if "log_level" in user_config and user_config["log_level"] not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            logging.warning(f"Invalid log_level: {user_config['log_level']}. Using default: INFO")
            user_config.pop("log_level")
            
        if "max_context_size" in user_config:
            try:
                max_context = int(user_config["max_context_size"])
                if max_context < 1 or max_context > 100:
                    logging.warning(f"Invalid max_context_size: {max_context}. Must be between 1 and 100. Using default: 10")
                    user_config.pop("max_context_size")
            except (ValueError, TypeError):
                logging.warning(f"Invalid max_context_size: {user_config['max_context_size']}. Using default: 10")
                user_config.pop("max_context_size")
                
        if "api_port" in user_config:
            try:
                port = int(user_config["api_port"])
                if port < 1024 or port > 65535:
                    logging.warning(f"Invalid api_port: {port}. Must be between 1024 and 65535. Using default: 8000")
                    user_config.pop("api_port")
            except (ValueError, TypeError):
                logging.warning(f"Invalid api_port: {user_config['api_port']}. Using default: 8000")
                user_config.pop("api_port")
                
        for url_key in ["chroma_url", "ollama_url"]:
            if url_key in user_config:
                url = user_config[url_key]
                if not url.startswith(("http://", "https://")):
                    logging.warning(f"Invalid {url_key}: {url}. URL must start with http:// or https://. Using default.")
                    user_config.pop(url_key)
        
        # Merge user config with default
        merged_config = {**default_config, **user_config}
        
        # Log the final configuration
        logging.info("Loaded configuration:")
        for key, value in merged_config.items():
            logging.info(f"  {key}: {value}")
            
        return merged_config
    except Exception as e:
        logging.error(f"Error loading config file: {e}")
        return default_config


def signal_handler(sig, frame):
    """Handle interruption signals.
    
    Args:
        sig: Signal number.
        frame: Current stack frame.
    """
    print("\nGracefully shutting down Jarvis...")
    sys.exit(0)


def run_interactive_mode(jarvis: JarvisEngine) -> None:
    """Run Jarvis in interactive mode.
    
    Args:
        jarvis: The initialized JarvisEngine instance.
    """
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Initial greeting (automatically detect language from system)
    import locale
    system_language = locale.getlocale()[0]
    language = "nl" if system_language and system_language.startswith("nl") else "en"
    
    print(jarvis.persona[language]["greeting"])
    print("----------------------------------------")
    
    # Main interaction loop
    while True:
        try:
            # Get user input
            user_input = input("> ").strip()
            
            # Exit command
            if user_input.lower() in ["exit", "quit", "stop", "bye", "afsluiten", "stoppen"]:
                language = jarvis.language.detect_language(user_input)
                print(jarvis.persona[language]["farewell"])
                break
            
            # Process input and get response
            if user_input:
                response = jarvis.process_input(user_input)
                print(response)
                print("----------------------------------------")
        
        except KeyboardInterrupt:
            # Handle Ctrl+C
            print("\nGoodbye! Jarvis is shutting down.")
            break
        
        except Exception as e:
            logging.error(f"Error in interaction: {e}")
            print("I'm sorry, I encountered an error. Please try again.")


def run_api_server(host: str, port: int) -> None:
    """Run the API server.
    
    Args:
        host: The host to bind to.
        port: The port to bind to.
    """
    uvicorn.run(app, host=host, port=port)


def main() -> None:
    """Main entry point for Jarvis AI Assistant."""
    global jarvis_instance
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Jarvis AI Assistant")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                        default="INFO", help="Logging level")
    parser.add_argument("--no-api", action="store_true", help="Disable API server")
    parser.add_argument("--no-cli", action="store_true", help="Disable CLI interface")
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.log_level)
    
    # Load configuration
    config = load_config(args.config)
    
    # Update config with command line arguments
    if args.log_level:
        config["log_level"] = args.log_level
    if args.no_api:
        config["enable_api"] = False
    if args.no_cli:
        config["enable_cli"] = False
    
    # Create and initialize Jarvis
    jarvis_instance = JarvisEngine(config)
    
    # Start API server if enabled
    api_thread = None
    if config.get("enable_api", True):
        logging.info(f"Starting API server on {config['api_host']}:{config['api_port']}")
        api_thread = threading.Thread(
            target=run_api_server,
            args=(config['api_host'], config['api_port']),
            daemon=True
        )
        api_thread.start()
    
    # Run CLI if enabled
    if config.get("enable_cli", True):
        run_interactive_mode(jarvis_instance)
    elif api_thread:
        # If CLI is disabled but API is enabled, wait for API thread
        try:
            api_thread.join()
        except KeyboardInterrupt:
            logging.info("Shutting down Jarvis...")
            sys.exit(0)


if __name__ == "__main__":
    main()