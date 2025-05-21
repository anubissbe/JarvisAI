FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the proxy port
EXPOSE 11435

# Command to run the proxy
CMD ["python", "/app/ollama_proxy.py"]
