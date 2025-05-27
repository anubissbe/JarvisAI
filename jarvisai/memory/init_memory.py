#!/usr/bin/env python3
"""
Initialize memory systems for JarvisAI-0.1.

This script sets up the memory databases with the required schemas and collections.
It should be run when the system starts up for the first time.
"""

import os
import sys
import logging
from typing import Dict, Any, List

import weaviate
from arango import ArangoClient
import redis
import chromadb

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
WEAVIATE_URL = os.getenv("VECTOR_DB_URL", "http://weaviate:8080")
ARANGO_URL = os.getenv("GRAPH_DB_URL", "http://arangodb:8529")
ARANGO_USER = os.getenv("ARANGO_USER", "root")
ARANGO_PASSWORD = os.getenv("ARANGO_ROOT_PASSWORD", "jarvisai")
CHROMA_URL = os.getenv("CHROMA_DB_URL", "http://chromadb:8000")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")


def init_weaviate() -> None:
    """Initialize Weaviate with required schemas."""
    try:
        client = weaviate.Client(WEAVIATE_URL)
        
        # Define schema for global knowledge
        global_knowledge_class = {
            "class": "GlobalKnowledge",
            "description": "Global knowledge shared across all users",
            "properties": [
                {
                    "name": "content",
                    "dataType": ["text"],
                    "description": "The actual knowledge content"
                },
                {
                    "name": "category",
                    "dataType": ["string"],
                    "description": "Knowledge category"
                },
                {
                    "name": "confidence",
                    "dataType": ["number"],
                    "description": "Confidence score for this knowledge"
                },
                {
                    "name": "sources",
                    "dataType": ["string[]"],
                    "description": "Sources for this knowledge"
                },
                {
                    "name": "created",
                    "dataType": ["date"],
                    "description": "Creation timestamp"
                },
                {
                    "name": "updated",
                    "dataType": ["date"],
                    "description": "Last update timestamp"
                }
            ]
        }
        
        # Define schema for user memories
        user_memory_class = {
            "class": "UserMemory",
            "description": "User-specific memories",
            "properties": [
                {
                    "name": "content",
                    "dataType": ["text"],
                    "description": "The actual memory content"
                },
                {
                    "name": "userId",
                    "dataType": ["string"],
                    "description": "User ID this memory belongs to",
                    "indexInverted": True
                },
                {
                    "name": "category",
                    "dataType": ["string"],
                    "description": "Memory category"
                },
                {
                    "name": "importance",
                    "dataType": ["number"],
                    "description": "Importance score for this memory"
                },
                {
                    "name": "created",
                    "dataType": ["date"],
                    "description": "Creation timestamp"
                },
                {
                    "name": "accessed",
                    "dataType": ["date"],
                    "description": "Last access timestamp"
                }
            ]
        }
        
        # Create schemas if they don't exist
        if not client.schema.contains(global_knowledge_class):
            client.schema.create_class(global_knowledge_class)
            logger.info("Created GlobalKnowledge schema in Weaviate")
        
        if not client.schema.contains(user_memory_class):
            client.schema.create_class(user_memory_class)
            logger.info("Created UserMemory schema in Weaviate")
            
    except Exception as e:
        logger.error(f"Failed to initialize Weaviate: {e}")
        raise


def init_arangodb() -> None:
    """Initialize ArangoDB with required collections."""
    try:
        client = ArangoClient(hosts=ARANGO_URL)
        sys_db = client.db("_system", username=ARANGO_USER, password=ARANGO_PASSWORD)
        
        # Create JarvisAI database if it doesn't exist
        if not sys_db.has_database("jarvisai"):
            sys_db.create_database("jarvisai")
            logger.info("Created JarvisAI database in ArangoDB")
        
        # Connect to JarvisAI database
        db = client.db("jarvisai", username=ARANGO_USER, password=ARANGO_PASSWORD)
        
        # Create document collections
        for collection_name in ["entities", "concepts"]:
            if not db.has_collection(collection_name):
                db.create_collection(collection_name)
                logger.info(f"Created {collection_name} collection in ArangoDB")
        
        # Create edge collections
        for edge_collection in ["relationships"]:
            if not db.has_collection(edge_collection):
                db.create_collection(edge_collection, edge=True)
                logger.info(f"Created {edge_collection} edge collection in ArangoDB")
                
    except Exception as e:
        logger.error(f"Failed to initialize ArangoDB: {e}")
        raise


def init_chromadb() -> None:
    """Initialize ChromaDB for recent memories."""
    try:
        client = chromadb.HttpClient(host="chromadb", port=8000)
        
        # Create collections for different temporal layers
        for collection_name in ["daily_memories", "weekly_memories"]:
            try:
                client.get_collection(collection_name)
                logger.info(f"Collection {collection_name} already exists in ChromaDB")
            except:
                client.create_collection(collection_name)
                logger.info(f"Created {collection_name} collection in ChromaDB")
                
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB: {e}")
        raise


def init_redis() -> None:
    """Initialize Redis for session memories."""
    try:
        # Remove redis:// prefix if present
        redis_url = REDIS_URL
        if redis_url.startswith("redis://"):
            redis_url = redis_url[8:]
            
        # Parse host and port
        if ":" in redis_url:
            host, port = redis_url.split(":")
        else:
            host, port = redis_url, 6379
            
        client = redis.Redis(host=host, port=int(port))
        
        # Test connection
        client.ping()
        logger.info("Successfully connected to Redis")
        
        # Redis doesn't need schema initialization
        # We'll create keys dynamically as needed
        
    except Exception as e:
        logger.error(f"Failed to initialize Redis: {e}")
        raise


def main() -> None:
    """Initialize all memory systems."""
    try:
        init_weaviate()
        init_arangodb()
        init_chromadb()
        init_redis()
        logger.info("All memory systems initialized successfully")
    except Exception as e:
        logger.error(f"Memory initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()