#!/bin/bash

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log files
LOG_FILE="jarvis.log"
ERROR_LOG="error.log"

# Function to log messages
log() {
    local message="$1"
    local level="$2"
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    
    case "$level" in
        "INFO")
            echo -e "${GREEN}[INFO]${NC} $message"
            echo "[$timestamp] [INFO] $message" >> "$LOG_FILE"
            ;;
        "WARN")
            echo -e "${YELLOW}[WARN]${NC} $message"
            echo "[$timestamp] [WARN] $message" >> "$LOG_FILE"
            ;;
        "ERROR")
            echo -e "${RED}[ERROR]${NC} $message"
            echo "[$timestamp] [ERROR] $message" >> "$LOG_FILE"
            echo "[$timestamp] [ERROR] $message" >> "$ERROR_LOG"
            ;;
        *)
            echo -e "$message"
            echo "[$timestamp] $message" >> "$LOG_FILE"
            ;;
    esac
}

# Function to check if a command exists
check_command() {
    local cmd="$1"
    if ! command -v "$cmd" &> /dev/null; then
        log "Command '$cmd' not found. Please install it." "ERROR"
        return 1
    fi
    return 0
}

# Function to check environment variables
check_env_vars() {
    local missing=0
    
    if [ ! -f .env ]; then
        log "No .env file found. Creating a template..." "WARN"
        echo "# JarvisAI Environment Variables" > .env
        echo "OPENAI_API_KEY=your_openai_api_key" >> .env
        echo "JWT_SECRET_KEY=your_jwt_secret_key" >> .env
        log "Please edit the .env file and add your API keys." "WARN"
        missing=1
    else
        # Source the .env file
        set -a
        source .env
        set +a
        
        if [ -z "$OPENAI_API_KEY" ]; then
            log "OPENAI_API_KEY is not set in .env file" "ERROR"
            missing=1
        fi
        
        if [ -z "$JWT_SECRET_KEY" ]; then
            log "JWT_SECRET_KEY is not set in .env file" "ERROR"
            missing=1
        fi
    fi
    
    return $missing
}

# Function to check Docker and Docker Compose
check_docker() {
    log "Checking Docker installation..." "INFO"
    
    if ! check_command "docker"; then
        log "Docker is required but not installed." "ERROR"
        log "Please install Docker: https://docs.docker.com/get-docker/" "ERROR"
        return 1
    fi
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        log "Docker is installed but not running." "ERROR"
        log "Please start Docker and try again." "ERROR"
        return 1
    fi
    
    log "Docker is installed and running." "INFO"
    
    # Check Docker Compose
    if ! check_command "docker-compose"; then
        log "Docker Compose is required but not installed." "ERROR"
        log "Please install Docker Compose: https://docs.docker.com/compose/install/" "ERROR"
        return 1
    fi
    
    log "Docker Compose is installed." "INFO"
    return 0
}

# Function to check if ports are available
check_ports() {
    local ports=("3000" "8000" "8081" "27017")
    local unavailable=0
    
    log "Checking if required ports are available..." "INFO"
    
    for port in "${ports[@]}"; do
        if lsof -i:"$port" &> /dev/null; then
            log "Port $port is already in use." "ERROR"
            unavailable=1
        fi
    done
    
    if [ $unavailable -eq 1 ]; then
        log "Please free up the required ports and try again." "ERROR"
        return 1
    fi
    
    log "All required ports are available." "INFO"
    return 0
}

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
    fi
    
    log "JarvisAI is now running!" "INFO"
    log "Access the application at:" "INFO"
    log "  - Frontend: http://localhost:3000" "INFO"
    log "  - Backend API: http://localhost:8000/docs" "INFO"
    log "  - MongoDB Express: http://localhost:8081" "INFO"
    
    return 0
}

# Function to monitor containers
monitor_containers() {
    log "Starting container monitoring..." "INFO"
    
    # Get container IDs
    local containers=$(docker-compose ps -q)
    
    if [ -z "$containers" ]; then
        log "No containers found to monitor." "ERROR"
        return 1
    fi
    
    log "Monitoring containers for errors..." "INFO"
    
    # Monitor container logs for errors
    docker-compose logs -f | grep -i "error\|exception\|fail" | tee -a "$ERROR_LOG" &
    local monitor_pid=$!
    
    # Check container health periodically
    while true; do
        for container in $containers; do
            local status=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null)
            local name=$(docker inspect --format='{{.Name}}' "$container" 2>/dev/null | sed 's/^\///')
            
            if [ "$status" != "running" ]; then
                log "Container $name is not running (status: $status)" "ERROR"
                
                # Get the last few lines of logs
                log "Last logs from $name:" "ERROR"
                docker logs --tail 20 "$container" >> "$ERROR_LOG" 2>&1
                
                # Try to restart the container
                log "Attempting to restart $name..." "WARN"
                docker start "$container" >> "$LOG_FILE" 2>> "$ERROR_LOG"
            fi
        done
        
        sleep 30
    done
    
    # Clean up
    kill $monitor_pid
}

# Function to stop the application
stop_app() {
    log "Stopping JarvisAI..." "INFO"
    docker-compose down 2>> "$ERROR_LOG" || {
        log "Failed to stop containers properly." "ERROR"
        return 1
    }
    log "JarvisAI has been stopped." "INFO"
    return 0
}

# Function to display status
show_status() {
    log "JarvisAI Status:" "INFO"
    docker-compose ps
    
    # Check if services are accessible
    if curl -s http://localhost:3000 &> /dev/null; then
        log "Frontend is accessible." "INFO"
    else
        log "Frontend is not accessible." "ERROR"
    fi
    
    if curl -s http://localhost:8000/docs &> /dev/null; then
        log "Backend API is accessible." "INFO"
    else
        log "Backend API is not accessible." "ERROR"
    fi
    
    if curl -s http://localhost:8081 &> /dev/null; then
        log "MongoDB Express is accessible." "INFO"
    else
        log "MongoDB Express is not accessible." "ERROR"
    fi
}

# Function to show logs
show_logs() {
    local service="$1"
    
    if [ -z "$service" ]; then
        docker-compose logs --tail=100
    else
        docker-compose logs --tail=100 "$service"
    fi
}

# Function to show errors
show_errors() {
    if [ -f "$ERROR_LOG" ]; then
        log "Showing error log:" "INFO"
        cat "$ERROR_LOG"
    else
        log "No error log found." "INFO"
    fi
}

# Function to clean up
cleanup() {
    log "Cleaning up..." "INFO"
    docker-compose down -v 2>> "$ERROR_LOG"
    log "Cleanup complete." "INFO"
}

# Main function
main() {
    # Initialize log files
    > "$LOG_FILE"
    > "$ERROR_LOG"
    
    log "JarvisAI Control Script" "INFO"
    log "======================" "INFO"
    
    # Process command line arguments
    local command="${1:-start}"
    
    case "$command" in
        "start")
            check_docker || exit 1
            check_env_vars || exit 1
            check_ports || exit 1
            start_app || exit 1
            
            # Ask if user wants to monitor
            read -p "Do you want to monitor containers for errors? (y/n): " monitor
            if [[ "$monitor" =~ ^[Yy]$ ]]; then
                monitor_containers
            else
                log "Monitoring skipped. You can check logs with './jarvis.sh logs'" "INFO"
            fi
            ;;
        "stop")
            stop_app
            ;;
        "restart")
            stop_app
            start_app
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs "$2"
            ;;
        "errors")
            show_errors
            ;;
        "clean")
            cleanup
            ;;
        *)
            log "Unknown command: $command" "ERROR"
            log "Usage: $0 [start|stop|restart|status|logs|errors|clean]" "INFO"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"