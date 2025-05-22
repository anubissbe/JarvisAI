FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    portaudio19-dev \
    python3-pyaudio \
    ffmpeg \
    alsa-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for audio files
RUN mkdir -p /app/audio

# Expose port for the speech service
EXPOSE 5000

# Command to run the speech service
CMD ["python", "speech_service.py"]