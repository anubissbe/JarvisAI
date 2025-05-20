#!/bin/bash
# start.sh - JarvisAI Setup and Launch Script
# This script automates the setup and launch of JarvisAI

# Set terminal colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse command-line arguments
SHOW_LOGS=false
DEBUG_MODE=false
for arg in "$@"; do
    case "$arg" in
        --logs|-l)
            SHOW_LOGS=true
            ;;
        --debug|-d)
            DEBUG_MODE=true
            ;;
    esac
done

if [ "$DEBUG_MODE" = true ]; then
    set -o errexit -o pipefail -o xtrace
    trap 'code=$?; echo -e "${RED}Error on line ${BASH_LINENO[0]}: exit code $code${NC}"' ERR
fi

if [ "$SHOW_LOGS" = true ]; then
    docker-compose logs -f
    exit $?
fi
# Print banner
echo -e "${BLUE}"
echo " █████  ███    ██ ██    ██ ██████  ██ ███████ ███████ ██████  ███████ "
echo "██   ██ ████   ██ ██    ██ ██   ██ ██ ██      ██      ██   ██ ██      "
echo "███████ ██ ██  ██ ██    ██ ██████  ██ ███████ ███████ ██████  █████   "
echo "██   ██ ██  ██ ██ ██    ██ ██   ██ ██      ██      ██ ██   ██ ██      "
echo "██   ██ ██   ████  ██████  ██████  ██ ███████ ███████ ██████  ███████ "
echo -e "${GREEN}"
echo "                       ██████  ██████  ███████ ███████ ███████ ███    ██ ████████ ███████ "
echo "                       ██   ██ ██   ██ ██      ██      ██      ████   ██    ██    ██      "
echo "                       ██████  ██████  █████   ███████ █████   ██ ██  ██    ██    ███████ "
echo "                       ██      ██   ██ ██           ██ ██      ██  ██ ██    ██         ██ "
echo "                       ██      ██   ██ ███████ ███████ ███████ ██   ████    ██    ███████ "
echo -e "${BLUE}"
echo "         ██ ███████ ██████  ██    ██ ██ ███████  █████  ██ "
echo "         ██ ██      ██   ██ ██    ██ ██ ██      ██   ██ ██ "
echo "         ██ █████   ██████  ██    ██ ██ ███████ ███████ ██ "
echo "    ██   ██ ██      ██   ██  ██  ██  ██      ██ ██   ██ ██ "
echo "     █████  ██      ██   ██   ████   ██ ███████ ██   ██ ██ "
echo -e "${NC}"
echo -e "${YELLOW}Self-Hosted RAG System with Knowledge Graph${NC}\n"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if user has sudo privileges
check_sudo() {
    echo -e "${BLUE}Checking for sudo privileges...${NC}"
    if sudo -v; then
        echo -e "${GREEN}Sudo privileges confirmed.${NC}"
    else
        echo -e "${RED}This script requires sudo privileges to install dependencies.${NC}"
        exit 1
    fi
}

# Function to install Docker
install_docker() {
    echo -e "${YELLOW}Installing Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    
    # Add current user to docker group
    sudo usermod -aG docker $USER
    
    # Install Docker Compose
    echo -e "${YELLOW}Installing Docker Compose...${NC}"
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    echo -e "${GREEN}Docker and Docker Compose have been installed.${NC}"
    echo -e "${YELLOW}You may need to log out and log back in for group changes to take effect.${NC}"
    echo -e "${YELLOW}If JarvisAI doesn't start, please try running this script again after logging back in.${NC}"
}

# Function to check and install NVIDIA Container Toolkit
install_nvidia_container_toolkit() {
    echo -e "${YELLOW}Installing NVIDIA Container Toolkit...${NC}"
    
    # Detect the Linux distribution
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [ "$ID" = "ubuntu" ] || [ "$ID_LIKE" = "ubuntu" ] || [ "$ID_LIKE" = "debian" ] || [ "$ID" = "debian" ]; then
            # Ubuntu/Debian-based
            distribution="ubuntu"
            curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
            curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
                sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
                sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
            sudo apt-get update
            sudo apt-get install -y nvidia-container-toolkit
        elif [ "$ID" = "centos" ] || [ "$ID" = "rhel" ] || [ "$ID" = "fedora" ] || [ "$ID_LIKE" = "rhel fedora" ]; then
            # RHEL/CentOS/Fedora
            distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
            sudo dnf config-manager --add-repo https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.repo
            sudo dnf install -y nvidia-container-toolkit
        else
            echo -e "${RED}Unsupported Linux distribution. Please install NVIDIA Container Toolkit manually.${NC}"
            echo -e "${YELLOW}Visit: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html${NC}"
            return 1
        fi
        
        # Configure Docker to use NVIDIA Container Toolkit
        sudo nvidia-ctk runtime configure --runtime=docker
        sudo systemctl restart docker
        
        echo -e "${GREEN}NVIDIA Container Toolkit has been installed and configured.${NC}"
    else
        echo -e "${RED}Could not determine the Linux distribution.${NC}"
        echo -e "${YELLOW}Please install NVIDIA Container Toolkit manually.${NC}"
        echo -e "${YELLOW}Visit: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html${NC}"
        return 1
    fi
}

# Check system requirements
check_system_requirements() {
    echo -e "${BLUE}Checking system requirements...${NC}"
    
    # Check CPU
    cpu_cores=$(nproc)
    if [ "$cpu_cores" -lt 4 ]; then
        echo -e "${YELLOW}Warning: JarvisAI recommends at least 4 CPU cores. You have $cpu_cores cores.${NC}"
    else
        echo -e "${GREEN}CPU: $cpu_cores cores available. ✓${NC}"
    fi
    
    # Check RAM
    mem_total=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$mem_total" -lt 16 ]; then
        echo -e "${YELLOW}Warning: JarvisAI recommends at least 16GB RAM. You have ${mem_total}GB.${NC}"
    else
        echo -e "${GREEN}RAM: ${mem_total}GB available. ✓${NC}"
    fi
    
    # Check disk space
    disk_space=$(df -h . | awk 'NR==2 {print $4}')
    echo -e "${GREEN}Disk space available: $disk_space${NC}"
    
    # Check for NVIDIA GPUs
    echo -e "${BLUE}Checking for NVIDIA GPUs...${NC}"
    if command_exists nvidia-smi; then
        gpu_info=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader)
        echo -e "${GREEN}NVIDIA GPUs detected:${NC}"
        echo -e "$gpu_info"
        has_nvidia_gpu=true
    else
        echo -e "${YELLOW}No NVIDIA GPUs detected or nvidia-smi not installed.${NC}"
        has_nvidia_gpu=false
    fi
}

# Configure environment
setup_environment() {
    echo -e "${BLUE}Setting up environment...${NC}"
    
    # Create .env file with a secure secret key
    if [ ! -f .env ]; then
        echo -e "${YELLOW}Creating .env file...${NC}"
        if command_exists openssl; then
            echo "WEBUI_SECRET_KEY=$(openssl rand -hex 32)" > .env
        else
            # Fallback if openssl isn't available
            random_string=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
            echo "WEBUI_SECRET_KEY=$random_string" > .env
        fi
        echo -e "${GREEN}.env file created with secure secret key.${NC}"
    else
        echo -e "${GREEN}.env file already exists.${NC}"
    fi
    
    # Ensure directory structure exists
    mkdir -p volumes/processed_documents logs tmp config hybrid_search proxy
    echo -e "${GREEN}Directory structure created.${NC}"
    
    # Create minimal hybrid_search/__init__.py if not exists
    if [ ! -f hybrid_search/__init__.py ]; then
        echo "" > hybrid_search/__init__.py
    fi
}

# Create or update the Jarvis model in Ollama
setup_jarvis_model() {
    echo -e "${BLUE}Setting up Jarvis model in Ollama...${NC}"
    
    # Wait for Ollama to be ready
    echo -e "${YELLOW}Waiting for Ollama to start...${NC}"
    max_attempts=30
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f "http://localhost:11434/api/tags" > /dev/null; then
            echo -e "\n${GREEN}Ollama is running.${NC}"
            break
        fi
        echo -n "."
        sleep 10
        attempt=$((attempt+1))
    done
    
    if [ $attempt -eq $max_attempts ]; then
        echo -e "\n${RED}Timed out waiting for Ollama to start. Check docker logs with 'docker-compose logs ollama'${NC}"
        return 1
    fi
    
    # Pull base model first
    echo -e "${YELLOW}Pulling llama3.1:8b base model...${NC}"
    pull_attempts=0
    pull_success=false
    while [ $pull_attempts -lt 3 ]; do
        curl -f -X POST "http://localhost:11434/api/pull" \
            -H "Content-Type: application/json" \
            -d '{"name": "llama3.1:8b"}' && pull_success=true && break
        echo -e "${RED}Failed to pull llama3.1:8b (attempt $((pull_attempts+1)))${NC}"
        pull_attempts=$((pull_attempts+1))
        sleep 5
    done
    if [ "$pull_success" != true ]; then
        echo -e "${RED}Unable to pull llama3.1:8b after $pull_attempts attempts.${NC}"
        return 1
    fi

    # Pull embedding model for RAG
    echo -e "${YELLOW}Pulling nomic-embed-text model...${NC}"
    pull_attempts=0
    pull_success=false
    while [ $pull_attempts -lt 3 ]; do
        curl -f -X POST "http://localhost:11434/api/pull" \
            -H "Content-Type: application/json" \
            -d '{"name": "nomic-embed-text"}' && pull_success=true && break
        echo -e "${RED}Failed to pull nomic-embed-text (attempt $((pull_attempts+1)))${NC}"
        pull_attempts=$((pull_attempts+1))
        sleep 5
    done
    if [ "$pull_success" != true ]; then
        echo -e "${RED}Unable to pull nomic-embed-text after $pull_attempts attempts.${NC}"
        return 1
    fi
    
    # Wait a moment for the pull to start
    sleep 5
    
    # Create the Jarvis model
    echo -e "${YELLOW}Creating Jarvis model from Modelfile...${NC}"
    
    # Using local file instead of base64 for better compatibility
    if [ -f Modelfile ]; then
        # Build Modelfile content for JSON payload
        # Convert newlines to spaces and escape quotes to avoid API errors
        modelfile_contents=$(cat Modelfile | sed 's/"/\\"/g' | tr '\n' ' ')
        create_attempts=0
        create_success=false
        while [ $create_attempts -lt 3 ]; do
            curl -f -s -X POST "http://localhost:11434/api/create" \
                -H "Content-Type: application/json" \
                -d "{\"name\": \"jarvis\", \"modelfile\": \"${modelfile_contents}\"}" && create_success=true && break
            echo -e "\n${RED}Failed to create Jarvis model (attempt $((create_attempts+1))).${NC}"
            create_attempts=$((create_attempts+1))
            sleep 5
        done
        if [ "$create_success" = true ]; then
            echo -e "\n${GREEN}Jarvis model creation initiated. This may take some time to complete.${NC}"
        else
            echo -e "\n${RED}Unable to create Jarvis model after $create_attempts attempts.${NC}"
            return 1
        fi
    else
        echo -e "\n${RED}Modelfile not found. Make sure it exists in the current directory.${NC}"
        return 1
    fi
}

# Set Jarvis as the default model in OpenWebUI
configure_openwebui() {
    echo -e "${BLUE}Configuring OpenWebUI...${NC}"
    
    # Wait for OpenWebUI to be ready
    echo -e "${YELLOW}Waiting for OpenWebUI to start...${NC}"
    max_attempts=30
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f "http://localhost:3000" > /dev/null; then
            echo -e "\n${GREEN}OpenWebUI is running.${NC}"
            break
        fi
        echo -n "."
        sleep 10
        attempt=$((attempt+1))
    done
    
    if [ $attempt -eq $max_attempts ]; then
        echo -e "\n${RED}Timed out waiting for OpenWebUI to start. Check docker logs with 'docker-compose logs open-webui'${NC}"
        return 1
    fi
    
    # Give additional time for OpenWebUI to fully initialize
    echo -e "${YELLOW}Giving OpenWebUI time to fully initialize...${NC}"
    sleep 20
    
    echo -e "${GREEN}OpenWebUI is ready.${NC}"
    echo -e "${YELLOW}To set Jarvis as your default model in OpenWebUI:${NC}"
    echo -e "${YELLOW}1. Login to OpenWebUI at http://localhost:3000${NC}"
    echo -e "${YELLOW}2. Go to Settings > Models${NC}"
    echo -e "${YELLOW}3. Select 'jarvis' from the dropdown and set as default${NC}"
}

# Start JarvisAI
start_jarvisai() {
    echo -e "${BLUE}Starting JarvisAI...${NC}"
    
    # Build and start the Docker containers
    echo -e "${YELLOW}Building and starting Docker containers...${NC}"
    if [ "$has_nvidia_gpu" = true ]; then
        echo -e "${GREEN}Starting with GPU support...${NC}"
        docker-compose up -d
    else
        echo -e "${YELLOW}Starting in CPU-only mode (performance will be limited)...${NC}"
        # Remove GPU-specific configurations when running without GPU
        sed 's/driver: nvidia/driver: none/g' docker-compose.yml > docker-compose-cpu.yml
        docker-compose -f docker-compose-cpu.yml up -d
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}JarvisAI services are starting up!${NC}"
        
        # Give containers time to initialize
        echo -e "${YELLOW}Waiting for services to initialize (this may take several minutes)...${NC}"
        sleep 30
        
        # Setup Jarvis model
        setup_jarvis_model
        
        # Configure OpenWebUI
        configure_openwebui
    else
        echo -e "${RED}Error starting JarvisAI services. Check the logs with 'docker-compose logs'.${NC}"
        exit 1
    fi
}

# Create Dockerfile for proxy if it doesn't exist
create_proxy_dockerfile() {
    if [ ! -f proxy/Dockerfile ]; then
        echo -e "${YELLOW}Creating Dockerfile for proxy service...${NC}"
        mkdir -p proxy
        cat > proxy/Dockerfile << EOF
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
EOF
        echo -e "${GREEN}Created proxy/Dockerfile${NC}"
    fi
}

# Monitor and provide status information
monitor_startup() {
    echo -e "${BLUE}Monitoring startup progress...${NC}"
    
    # Wait a bit to let containers start
    sleep 10
    
    # Check status of key services
    echo -e "${YELLOW}Current status of JarvisAI services:${NC}"
    docker-compose ps
    
    # Provide log access instructions
    echo -e "\n${YELLOW}To view logs of specific services:${NC}"
    echo -e "${GREEN}docker-compose logs -f ollama${NC} - For the Ollama LLM service"
    echo -e "${GREEN}docker-compose logs -f open-webui${NC} - For the web interface"
    echo -e "${GREEN}docker-compose logs -f neo4j${NC} - For the knowledge graph database"
    echo -e "${GREEN}docker-compose logs -f document-processor${NC} - For document processing status"
}

# Main execution
main() {
    echo -e "${BLUE}Starting JarvisAI setup...${NC}"
    
    # Check for sudo privileges
    check_sudo
    
    # Check system requirements
    check_system_requirements
    
    # Check if Docker is installed
    if command_exists docker; then
        echo -e "${GREEN}Docker is already installed.${NC}"
        # Check Docker version
        docker_version=$(docker --version | cut -d ' ' -f3 | cut -d ',' -f1)
        echo -e "${GREEN}Docker version: $docker_version${NC}"
    else
        echo -e "${YELLOW}Docker is not installed.${NC}"
        install_docker
    fi
    
    # Check Docker Compose
    if command_exists docker-compose; then
        echo -e "${GREEN}Docker Compose is already installed.${NC}"
        # Check Docker Compose version
        compose_version=$(docker-compose --version | cut -d ' ' -f3 | cut -d ',' -f1)
        echo -e "${GREEN}Docker Compose version: $compose_version${NC}"
    else
        echo -e "${YELLOW}Docker Compose is not installed.${NC}"
        sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        echo -e "${GREEN}Docker Compose has been installed.${NC}"
    fi
    
    # Check for NVIDIA Container Toolkit if GPU is available
    if [ "$has_nvidia_gpu" = true ]; then
        if docker info 2>/dev/null | grep -q "Runtimes:.*nvidia"; then
            echo -e "${GREEN}NVIDIA Container Toolkit is already configured.${NC}"
        else
            echo -e "${YELLOW}NVIDIA Container Toolkit needs to be installed or configured.${NC}"
            install_nvidia_container_toolkit
        fi
    else
        echo -e "${YELLOW}No NVIDIA GPU detected, skipping NVIDIA Container Toolkit setup.${NC}"
        echo -e "${YELLOW}JarvisAI will run in CPU-only mode, which may be significantly slower.${NC}"
    fi
    
    # Setup environment
    setup_environment
    
    # Create proxy Dockerfile if needed
    create_proxy_dockerfile
    
    # Start JarvisAI
    start_jarvisai
    
    # Monitor startup
    monitor_startup
    
    # Provide information on how to access the system
    echo -e "\n${GREEN}Setup initiated!${NC}"
    echo -e "${BLUE}JarvisAI is starting up. This may take several minutes to hours for all services to initialize.${NC}"
    echo -e "${BLUE}  - Large models need to be downloaded (10GB+)${NC}"
    echo -e "${BLUE}  - Databases need to be initialized${NC}"
    echo -e "${BLUE}  - Services need to connect with each other${NC}"
    echo -e "\n${BLUE}You can access the web interface at:${NC} ${GREEN}http://localhost:3000${NC}"
    echo -e "${BLUE}Default credentials (if prompted):${NC} ${GREEN}admin / password${NC} ${YELLOW}(change this immediately!)${NC}"
    
    # Warning about initial startup time
    echo -e "\n${YELLOW}Note: The initial startup may take 30+ minutes as models are downloaded and initialized.${NC}"
    echo -e "${YELLOW}The Jarvis model setup will continue in the background. Check status with:${NC}"
    echo -e "${GREEN}curl http://localhost:11434/api/tags${NC}"
    
    # Provide info on uploading documents
    echo -e "\n${BLUE}After setup is complete, upload documents to your knowledge base:${NC}"
    echo -e "${GREEN}1. Access the web interface at http://localhost:3000${NC}"
    echo -e "${GREEN}2. Go to the 'Knowledge' tab${NC}"
    echo -e "${GREEN}3. Create a new knowledge base or use the default${NC}"
    echo -e "${GREEN}4. Upload your documents${NC}"
    echo -e "${GREEN}5. Choose 'jarvis' model in chat to leverage your knowledge base${NC}"
}

# Run the main function
main

# Exit with a success message
echo -e "\n${GREEN}Start script completed. Enjoy using JarvisAI!${NC}"
