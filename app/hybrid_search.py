# ... existing code ...

import time
import requests
from requests.exceptions import Timeout

# ... existing code ...

def generate_embeddings(self, text, timeout=30):
    """Generate embeddings for text using Ollama API with timeout."""
    start_time = time.time()
    self.logger.info(f"Generating embeddings for text of length {len(text)}")
    
    try:
        response = requests.post(
            f"{self.ollama_api_base}/api/embeddings",
            json={"model": self.embedding_model, "prompt": text},
            timeout=timeout  # Add timeout parameter
        )
        
        if response.status_code == 200:
            embeddings = response.json().get("embedding", [])
            embed_time = time.time() - start_time
            self.logger.info(f"Embeddings generated in {embed_time:.2f}s")
            return embeddings
        else:
            self.logger.error(f"Failed to generate embeddings: {response.status_code} - {response.text}")
            return []
            
    except Timeout:
        self.logger.error(f"Timeout after {timeout}s while generating embeddings")
        return []
    except Exception as e:
        self.logger.error(f"Error generating embeddings: {str(e)}")
        return []