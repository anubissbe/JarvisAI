FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install additional Python packages for rate limiting
RUN pip install fastapi-limiter redis slowapi

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy only application code to limit build context
COPY requirements.txt .
COPY src/ ./src/

# Create necessary directories
RUN mkdir -p /root/.jarvis/memory /root/.jarvis/knowledge /root/.jarvis/logs

# Add Python path
ENV PYTHONPATH="/app:/app/src:${PYTHONPATH}"
ENV LOG_LEVEL="INFO"

# Expose port for API
EXPOSE 8000

# Change working directory to src
WORKDIR /app/src

# Command to run the application
CMD ["python", "-m", "main", "--no-cli"]