# Use multi-stage build for a smaller final image
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install spacy language models
RUN python -m spacy download en_core_web_sm && \
    python -m spacy download nl_core_news_sm && \
    python -m spacy download de_core_news_sm

# Final stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONWARNINGS="ignore::UserWarning,ignore::FutureWarning" \
    TZ=UTC

# Create non-root user
RUN useradd -m -u 1000 jarvis

# Set up working directory
WORKDIR /app
RUN mkdir -p /app/data /app/logs && \
    chown -R jarvis:jarvis /app

# Copy source code
COPY --chown=jarvis:jarvis src/ ./src/

# Switch to non-root user
USER jarvis

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run the application
CMD ["python", "src/main.py"]