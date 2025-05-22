FROM python:3.10-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir flask requests

# Copy application code
COPY . .

# Expose the proxy port
EXPOSE 11435

# Command to run the proxy
CMD ["python", "ollama_proxy.py"]