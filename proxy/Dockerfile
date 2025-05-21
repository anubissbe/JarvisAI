FROM python:3.10-slim

WORKDIR /app

# Install runtime dependencies
RUN pip install --no-cache-dir \
    marshmallow==3.19.0 \
    environs==9.5.0

# Install dependencies with specific versions for consistency
RUN pip install --no-cache-dir flask==3.1.1 requests==2.31.0 neo4j==5.28.1 pymilvus==2.3.3

# Copy application code
COPY . .

# Expose the proxy port
EXPOSE 11435

# Command to run the proxy
CMD ["python", "ollama_proxy.py"]
