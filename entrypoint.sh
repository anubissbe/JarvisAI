#!/bin/bash
set -e

# Initialize JarvisAI components
echo "Initializing JarvisAI-0.1..."

# Wait for dependencies to be ready
echo "Waiting for dependencies..."
python -c "
import time
import socket
import sys

services = [
    ('weaviate', 8080),
    ('arangodb', 8529),
    ('chromadb', 8000),
    ('redis', 6379),
    ('ollama', 11434)
]

timeout = 300  # 5 minutes timeout
start_time = time.time()

for service, port in services:
    elapsed = 0
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect((service, port))
            sock.close()
            print(f'{service} is ready')
            break
        except (socket.error, socket.timeout):
            elapsed = time.time() - start_time
            if elapsed > timeout:
                print(f'Timeout waiting for {service}', file=sys.stderr)
                sys.exit(1)
            time.sleep(2)
"

# Initialize memory systems
echo "Initializing memory systems..."
python -m jarvisai.memory.init_memory || true

# Start the original entrypoint
echo "Starting Open-WebUI with JarvisAI extensions..."
exec /app/entrypoint.sh