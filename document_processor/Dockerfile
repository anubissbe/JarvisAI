FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    libreoffice \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for documents
RUN mkdir -p /app/uploads /app/processed_documents

# Command to run the document processor
CMD ["python", "processor.py"]