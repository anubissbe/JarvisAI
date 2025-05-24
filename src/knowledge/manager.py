import os
import io
import json
import hashlib
import aiohttp
import asyncio
import aiofiles
import warnings
import logging
import time
from typing import Dict, List, Any, Optional, Union, BinaryIO
from datetime import datetime
import chromadb
from chromadb.config import Settings
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
from fastapi import UploadFile, HTTPException
import PyPDF2
import docx
from bs4 import BeautifulSoup
import magic  # python-magic for file type detection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Filter out specific deprecation warnings
warnings.filterwarnings("ignore", category=UserWarning, 
                       message=".*_register_pytree_node is deprecated.*")
warnings.filterwarnings("ignore", category=FutureWarning, 
                       message=".*resume_download is deprecated.*")

class CustomSentenceTransformerEmbedding(EmbeddingFunction):
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        from sentence_transformers import SentenceTransformer
        # Disable transformers warnings during model loading
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.model = SentenceTransformer(model_name)
            self.batch_size = 32  # Configurable batch size for memory efficiency

    def __call__(self, input: Documents) -> Embeddings:
        if not input:
            return []
        
        # Process in batches
        all_embeddings = []
        for i in range(0, len(input), self.batch_size):
            batch = input[i:i + self.batch_size]
            embeddings = self.model.encode(batch, convert_to_tensor=True)
            all_embeddings.extend(embeddings.tolist())
        
        return all_embeddings

class DocumentProcessor:
    """Handles different document types and extracts text content"""
    
    def __init__(self):
        self.mime = magic.Magic(mime=True)
    
    async def process_document(self, file: Union[UploadFile, BinaryIO, str]) -> str:
        """Process different document types and return extracted text"""
        try:
            if isinstance(file, str):
                # Handle URL
                if file.startswith(('http://', 'https://')):
                    return await self._process_url(file)
                # Handle file path
                return await self._process_file_path(file)
            
            # Read file content
            if isinstance(file, UploadFile):
                content = await file.read()
            else:
                content = file.read()
            
            # Detect file type
            file_type = self.mime.from_buffer(content)
            
            # Process based on file type
            if file_type == 'application/pdf':
                return self._process_pdf(io.BytesIO(content))
            elif file_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                return self._process_docx(io.BytesIO(content))
            elif file_type.startswith('text/'):
                return content.decode('utf-8')
            elif file_type == 'text/html':
                return self._process_html(content.decode('utf-8'))
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}", exc_info=True)
            raise
    
    def _process_pdf(self, file_obj: io.BytesIO) -> str:
        """Extract text from PDF file"""
        text = []
        pdf = PyPDF2.PdfReader(file_obj)
        for page in pdf.pages:
            text.append(page.extract_text())
        return "\n".join(text)
    
    def _process_docx(self, file_obj: io.BytesIO) -> str:
        """Extract text from DOCX file"""
        doc = docx.Document(file_obj)
        return "\n".join(paragraph.text for paragraph in doc.paragraphs)
    
    def _process_html(self, content: str) -> str:
        """Extract text from HTML content"""
        soup = BeautifulSoup(content, 'html.parser')
        return soup.get_text(separator="\n")
    
    async def _process_url(self, url: str) -> str:
        """Fetch and process content from URL"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                content_type = response.headers.get('content-type', '')
                content = await response.read()
                
                if 'pdf' in content_type:
                    return self._process_pdf(io.BytesIO(content))
                elif 'html' in content_type:
                    return self._process_html(content.decode('utf-8'))
                elif 'text' in content_type:
                    return content.decode('utf-8')
                else:
                    raise ValueError(f"Unsupported content type from URL: {content_type}")
    
    async def _process_file_path(self, file_path: str) -> str:
        """Process a file from the file system"""
        async with aiofiles.open(file_path, 'rb') as f:
            content = await f.read()
            file_type = self.mime.from_buffer(content)
            
            if file_type == 'application/pdf':
                return self._process_pdf(io.BytesIO(content))
            elif file_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                return self._process_docx(io.BytesIO(content))
            elif file_type.startswith('text/'):
                return content.decode('utf-8')
            else:
                raise ValueError(f"Unsupported file type: {file_type}")

class KnowledgeManager:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        # Set up configuration
        self.chromadb_host = os.getenv("CHROMADB_HOST", "localhost")
        self.chromadb_port = int(os.getenv("CHROMADB_PORT", "8000"))
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize components
        self.client = None
        self.collection = None
        self.embedding_function = None
        self.document_processor = DocumentProcessor()
        
        # Initialize metrics
        self.metrics = {
            "documents_processed": 0,
            "total_chunks": 0,
            "failed_documents": 0,
            "total_tokens": 0
        }
        
        # Initialize ChromaDB
        self._init_chromadb()

    def _init_chromadb(self, max_retries=5, retry_delay=5):
        """Initialize ChromaDB client with retries"""
        retries = 0
        last_error = None

        while retries < max_retries:
            try:
                logger.info(f"Attempting to connect to ChromaDB at {self.chromadb_host}:{self.chromadb_port} (attempt {retries + 1}/{max_retries})")
                
                # Initialize client with optimized settings
                self.client = chromadb.HttpClient(
                    host=self.chromadb_host,
                    port=self.chromadb_port,
                    settings=Settings(
                        allow_reset=True,
                        anonymized_telemetry=False,
                        persist_directory="/app/data/chromadb",
                        is_persistent=True
                    )
                )

                # Set up embedding function with error handling
                try:
                    self.embedding_function = CustomSentenceTransformerEmbedding()
                except Exception as e:
                    logger.error(f"Failed to initialize embedding function: {str(e)}")
                    raise
                
                # Create or get collection with optimized settings
                self.collection = self.client.get_or_create_collection(
                    name="jarvis_knowledge",
                    embedding_function=self.embedding_function,
                    metadata={
                        "description": "Jarvis AI Knowledge Base",
                        "created_at": datetime.utcnow().isoformat(),
                        "chunk_size": self.chunk_size,
                        "chunk_overlap": self.chunk_overlap
                    }
                )
                
                logger.info("Successfully connected to ChromaDB and initialized collection")
                return
            
            except Exception as e:
                last_error = e
                logger.warning(f"Failed to connect to ChromaDB: {str(e)}")
                retries += 1
                if retries < max_retries:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)

        logger.error("Failed to connect to ChromaDB after maximum retries")
        raise last_error

    async def add_document(
        self,
        document: Union[UploadFile, Dict[str, Any], str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a document to the knowledge base.
        Returns document details including ID and processing metrics.
        """
        try:
            start_time = time.time()
            
            # Process document content
            content = await self.document_processor.process_document(document)
            
            # Generate document ID
            doc_id = self._generate_doc_id(content)
            
            # Prepare base metadata
            base_metadata = {
                "source": metadata.get("source", "unknown") if metadata else "unknown",
                "type": metadata.get("type", "text") if metadata else "text",
                "timestamp": datetime.utcnow().isoformat(),
                "doc_id": doc_id,
                **(metadata or {})
            }
            
            # Split content into chunks with improved chunking
            chunks = await self._chunk_text(content)
            
            # Process chunks in batches
            batch_size = 50
            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i:i + batch_size]
                chunk_ids = [f"{doc_id}_chunk_{j}" for j in range(i, i + len(batch_chunks))]
                chunk_metadata = [{**base_metadata, "chunk_id": j} for j in range(i, i + len(batch_chunks))]
                
                # Add batch to ChromaDB
                self.collection.add(
                    documents=batch_chunks,
                    metadatas=chunk_metadata,
                    ids=chunk_ids
                )
            
            # Update metrics
            self.metrics["documents_processed"] += 1
            self.metrics["total_chunks"] += len(chunks)
            self.metrics["total_tokens"] += sum(len(chunk.split()) for chunk in chunks)
            
            processing_time = time.time() - start_time
            
            # Return detailed result
            return {
                "doc_id": doc_id,
                "chunks_created": len(chunks),
                "processing_time_seconds": processing_time,
                "metadata": base_metadata,
                "status": "success"
            }
            
        except Exception as e:
            self.metrics["failed_documents"] += 1
            logger.error(f"Error adding document: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Failed to process document",
                    "message": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

    async def search_relevant_info(
        self,
        query: str,
        limit: int = 5,
        min_relevance_score: float = 0.5
    ) -> Dict[str, Any]:
        """
        Search for relevant information in the knowledge base.
        Returns a dictionary with relevant text, sources, and relevance scores.
        """
        try:
            # Query ChromaDB for relevant chunks with metadata
            results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                include_metadata=True,
                include_distances=True
            )
            
            # Process and combine results
            combined_info = {
                "text": [],
                "sources": set(),
                "relevance_scores": [],
                "chunks": []
            }
            
            if results and results['documents']:
                # Convert distances to similarity scores (1 - normalized_distance)
                max_distance = max(results['distances'][0]) if results['distances'][0] else 1
                similarities = [1 - (d / max_distance) for d in results['distances'][0]]
                
                # Filter and sort by relevance
                filtered_results = []
                for doc, metadata, similarity in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    similarities
                ):
                    if similarity >= min_relevance_score:
                        filtered_results.append({
                            "text": doc,
                            "metadata": metadata,
                            "relevance": similarity
                        })
                
                # Sort by relevance
                filtered_results.sort(key=lambda x: x["relevance"], reverse=True)
                
                # Combine results
                for result in filtered_results:
                    combined_info["text"].append(result["text"])
                    if result["metadata"].get("source"):
                        combined_info["sources"].add(result["metadata"]["source"])
                    combined_info["relevance_scores"].append(result["relevance"])
                    combined_info["chunks"].append({
                        "text": result["text"],
                        "metadata": result["metadata"],
                        "relevance": result["relevance"]
                    })
            
            return {
                "text": "\n".join(combined_info["text"]),
                "sources": list(combined_info["sources"]),
                "relevance_scores": combined_info["relevance_scores"],
                "chunks": combined_info["chunks"],
                "query_timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error searching knowledge base: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Failed to search knowledge base",
                    "message": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

    def _generate_doc_id(self, content: str) -> str:
        """Generate a unique document ID based on content hash"""
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        return f"doc_{timestamp}_{content_hash[:16]}"

    async def _chunk_text(self, text: str) -> List[str]:
        """Split text into smaller chunks with improved chunking strategy"""
        try:
            # Normalize text
            text = text.replace('\r\n', '\n').strip()
            
            # Split into paragraphs first
            paragraphs = text.split('\n\n')
            
            chunks = []
            current_chunk = []
            current_size = 0
            
            for paragraph in paragraphs:
                # Clean paragraph
                paragraph = paragraph.strip()
                if not paragraph:
                    continue
                
                # If paragraph is too large, split it into sentences
                if len(paragraph) > self.chunk_size:
                    sentences = paragraph.replace('\n', ' ').split('. ')
                    for sentence in sentences:
                        sentence = sentence.strip()
                        if not sentence:
                            continue
                        
                        # If adding this sentence would exceed chunk size
                        if current_size + len(sentence) + 1 > self.chunk_size:
                            if current_chunk:
                                chunks.append(' '.join(current_chunk))
                                current_chunk = []
                                current_size = 0
                        
                        current_chunk.append(sentence)
                        current_size += len(sentence) + 1
                else:
                    # If adding this paragraph would exceed chunk size
                    if current_size + len(paragraph) + 2 > self.chunk_size:
                        if current_chunk:
                            chunks.append(' '.join(current_chunk))
                            current_chunk = []
                            current_size = 0
                    
                    current_chunk.append(paragraph)
                    current_size += len(paragraph) + 2
            
            # Add the last chunk if it exists
            if current_chunk:
                chunks.append(' '.join(current_chunk))
            
            # Ensure overlap between chunks
            if self.chunk_overlap > 0 and len(chunks) > 1:
                overlapped_chunks = []
                for i in range(len(chunks)):
                    if i > 0:
                        # Add overlap from previous chunk
                        words = chunks[i-1].split()
                        overlap = ' '.join(words[-self.chunk_overlap:])
                        chunks[i] = overlap + ' ' + chunks[i]
                    overlapped_chunks.append(chunks[i])
                chunks = overlapped_chunks
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error chunking text: {str(e)}", exc_info=True)
            raise

    async def health_check(self) -> bool:
        """Check if the knowledge base is healthy"""
        try:
            # Test basic operations
            test_id = f"health_check_{datetime.utcnow().isoformat()}"
            test_content = "Health check test document"
            
            # Test adding document
            self.collection.add(
                documents=[test_content],
                metadatas=[{"type": "health_check"}],
                ids=[test_id]
            )
            
            # Test querying
            results = self.collection.query(
                query_texts=["health check"],
                n_results=1
            )
            
            # Test deletion
            self.collection.delete(ids=[test_id])
            
            return True
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}", exc_info=True)
            return False

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics of the knowledge base"""
        return {
            **self.metrics,
            "timestamp": datetime.utcnow().isoformat()
        }