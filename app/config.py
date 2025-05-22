# ... existing code ...

# Document processing settings
MAX_DOCUMENT_SIZE_MB = int(os.getenv("MAX_DOCUMENT_SIZE_MB", "10"))  # Default 10MB
MAX_CHUNK_SIZE = int(os.getenv("MAX_CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
EMBEDDING_TIMEOUT = int(os.getenv("EMBEDDING_TIMEOUT", "60"))  # 60 seconds timeout

# ... existing code ...