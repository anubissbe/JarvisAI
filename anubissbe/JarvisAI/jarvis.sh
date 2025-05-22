# ... existing code ...

# Function to start the application
start_app() {
    log "Starting JarvisAI..." "INFO"
    
    # Pull latest images
    log "Pulling latest Docker images..." "INFO"
    docker-compose pull 2>> "$ERROR_LOG" || {
        log "Failed to pull Docker images." "ERROR"
        return 1
    }
    
    # Build and start containers
    log "Building and starting containers..." "INFO"
    docker-compose up -d --build 2>> "$ERROR_LOG" || {
        log "Failed to start containers." "ERROR"
        return 1
    }
    
    log "JarvisAI is starting up. This may take a moment..." "INFO"
    
    # Wait for services to be ready
    log "Waiting for services to be ready..." "INFO"
    
    # Wait for backend to be ready
    local max_attempts=30
    local attempt=0
    local backend_ready=0
    
    while [ $attempt -lt $max_attempts ] && [ $backend_ready -eq 0 ]; do
        if curl -s http://localhost:8000/docs &> /dev/null; then
            backend_ready=1
        else
            attempt=$((attempt + 1))
            sleep 2
        fi
    done
    
    if [ $backend_ready -eq 0 ]; then
        log "Backend service did not become ready in time." "ERROR"
        return 1
    }
    
    # Pull required Ollama models
    log "Pulling required Ollama models..." "INFO"
    docker exec -it $(docker-compose ps -q ollama) ollama pull llama3 2>> "$ERROR_LOG" || {
        log "Warning: Failed to pull llama3 model. You may need to pull it manually." "WARN"
    }
    
    docker exec -it $(docker-compose ps -q ollama) ollama pull nomic-embed-text-v1.5 2>> "$ERROR_LOG" || {
        log "Warning: Failed to pull nomic-embed-text-v1.5 model. You may need to pull it manually." "WARN"
    }
    
    log "JarvisAI is now running!" "INFO"
    log "Access the application at:" "INFO"
    log "  - Frontend: http://localhost:3000" "INFO"
    log "  - Backend API: http://localhost:8000/docs" "INFO"
    log "  - MongoDB Express: http://localhost:8081" "INFO"
    
    # First-time setup guidance
    log "" "INFO"
    log "First-time setup instructions:" "INFO"
    log "  1. Navigate to http://localhost:3000 in your browser" "INFO"
    log "  2. Register a new user account" "INFO"
    log "  3. Log in with your new credentials" "INFO"
    log "  4. Go to Settings to configure AI model, voice, and integrations" "INFO"
    log "  5. Go to Knowledge Base to upload documents" "INFO"
    log "  6. Return to Dashboard to start interacting with JarvisAI" "INFO"
    log "" "INFO"
    
    return 0
}

# ... existing code ...