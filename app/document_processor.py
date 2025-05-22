# ... existing code ...
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("document_processor")

# ... existing code ...

# In your document processing function:
def process_document(document_id, file_path, ...):
    start_time = time.time()
    file_size = os.path.getsize(file_path)
    logger.info(f"Starting to process document ID: {document_id}, size: {file_size} bytes")
    
    # After parsing
    logger.info(f"Document parsed, extracting content")
    
    # After content extraction
    logger.info(f"Content extracted, creating chunks")
    
    # Before embedding generation
    chunk_count = len(chunks)
    logger.info(f"Created {chunk_count} chunks, generating embeddings")
    
    # After embedding generation
    logger.info(f"Embeddings generated, storing in vector database")
    
    # At completion
    processing_time = time.time() - start_time
    logger.info(f"Document processing completed: {document_id} in {processing_time:.2f} seconds")

# ... existing code ...