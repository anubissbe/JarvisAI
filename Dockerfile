FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create necessary directories
RUN mkdir -p /root/.jarvis/memory /root/.jarvis/knowledge /root/.jarvis/logs

# Set environment variables
ENV PYTHONPATH="${PYTHONPATH}:/app"
ENV LOG_LEVEL="INFO"

# Expose port for API
EXPOSE 8000

# Command to run the application
CMD ["python", "-m", "src.main"]