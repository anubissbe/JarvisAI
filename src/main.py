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
from typing import Dict, Any, Optional
import threading
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core import JarvisEngine

# Initialize FastAPI
app = FastAPI(title="Jarvis AI API", description="API for Jarvis AI Assistant", version="0.1.0")

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    return {"status": "healthy"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint."""
    global jarvis_instance
    if not jarvis_instance:
        return {"error": "Jarvis is not initialized"}
    
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


@app.post("/web-search", response_model=WebSearchResponse)
async def web_search(request: WebSearchRequest):
    """Web search endpoint."""
    global jarvis_instance
    if not jarvis_instance:
        return {"error": "Jarvis is not initialized"}
    
    # Detect language if not specified
    language = request.language
    if not language:
        language = jarvis_instance.language.detect_language(request.query)
    
    # Perform web search
    results = jarvis_instance.knowledge.web_search.search(
        query=request.query,
        language=language
    )
    
    return WebSearchResponse(results=results)


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


@app.post("/knowledge/add", response_model=KnowledgeAddResponse)
async def add_knowledge(request: KnowledgeAddRequest):
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
    
    # Configure logging
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(logs_dir, "jarvis.log")),
            logging.StreamHandler(sys.stdout)
        ]
    )


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
        
        # Merge user config with default
        merged_config = {**default_config, **user_config}
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