# ... existing code ...

from config import MAX_DOCUMENT_SIZE_MB, MAX_CHUNK_SIZE, CHUNK_OVERLAP, EMBEDDING_TIMEOUT

# ... existing code ...

def process_document(self, file_path, kb_id=None):
    """Process a document and add it to the knowledge base."""
    start_time = time.time()
    
    # Check file size
    file_size_bytes = os.path.getsize(file_path)
    file_size_mb = file_size_bytes / (1024 * 1024)
    self.logger.info(f"Starting to process document: {os.path.basename(file_path)}, size: {file_size_mb:.2f} MB")
    
    if file_size_mb > MAX_DOCUMENT_SIZE_MB:
        self.logger.error(f"Document too large: {file_size_mb:.2f} MB exceeds limit of {MAX_DOCUMENT_SIZE_MB} MB")
        return False
    
    # ... rest of the existing code ...
    
    # Update chunk creation with config values
    chunks = self.create_chunks(document_content, chunk_size=MAX_CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    
    # ... rest of the existing code ...
    
    # Pass timeout to embedding generation
    embeddings = self.hybrid_search.generate_embeddings(chunk_text, timeout=EMBEDDING_TIMEOUT)
    
    # ... rest of the existing code ...