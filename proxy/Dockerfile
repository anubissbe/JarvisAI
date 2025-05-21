FROM python:3.10-slim

WORKDIR /app

# Install specific versions of marshmallow and environs first to avoid conflicts
RUN pip install --no-cache-dir \
    marshmallow==3.19.0 \
    environs==9.5.0

# Install dependencies with specific versions for consistency
RUN pip install --no-cache-dir \
    flask==2.3.3 \
    requests==2.31.0 \
    neo4j==5.12.0 \
    pymilvus==2.3.3

# Copy application code
COPY . .

# Expose the proxy port
EXPOSE 11435

# Command to run the proxy
CMD ["python", "ollama_proxy.py"]