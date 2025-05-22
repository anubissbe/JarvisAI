# ... existing code ...

import os
import logging
import tempfile
from typing import List, Dict, Any, Optional
import PyPDF2
import docx
import csv
import requests
import numpy as np
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS

from models.db.document import DocumentDB

logger = logging.getLogger(__name__)

class OllamaEmbeddings:
    """Ollama embeddings implementation"""
    
    def __init__(self, model_name="nomic-embed-text-v1.5", base_url="http://ollama:11434"):
        self.model_name = model_name
        self.base_url = base_url
        
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed documents using Ollama API"""
        embeddings = []
        for text in texts:
            embedding = self._get_embedding(text)
            embeddings.append(embedding)
        return embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """Embed query using Ollama API"""
        return self._get_embedding(text)
    
    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text"""
        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model_name, "prompt": text}
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            logger.error(f"Error getting embedding from Ollama: {str(e)}")
            # Return a zero vector as fallback
            return [0.0] * 768  # nomic-embed-text-v1.5 uses 768-dimensional embeddings

class DocumentProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        # Use Ollama embeddings instead of OpenAI
        self.embeddings = OllamaEmbeddings()
        self.vector_store = None
        self._load_vector_store()
    
# ... existing code ...