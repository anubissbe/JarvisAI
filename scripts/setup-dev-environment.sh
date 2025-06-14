#!/bin/bash
# Setup script for development environment with single GPU (RTX 5090 32GB)

echo "🚀 JarvisAI Development Environment Setup"
echo "========================================"
echo "GPU: NVIDIA RTX 5090 (32GB VRAM)"
echo ""

# Check for NVIDIA GPU
if ! nvidia-smi > /dev/null 2>&1; then
    echo "❌ Error: NVIDIA GPU not detected"
    echo "Please ensure NVIDIA drivers are installed"
    exit 1
fi

echo "✅ GPU Detected:"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
echo ""

# Check Docker
if ! docker --version > /dev/null 2>&1; then
    echo "❌ Error: Docker not installed"
    echo "Please install Docker first"
    exit 1
fi

# Check Docker Compose
if ! docker compose version > /dev/null 2>&1; then
    echo "❌ Error: Docker Compose not installed"
    exit 1
fi

# Check NVIDIA Container Toolkit
if ! docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi > /dev/null 2>&1; then
    echo "❌ Error: NVIDIA Container Toolkit not installed"
    echo "Please install nvidia-container-toolkit"
    exit 1
fi

echo "✅ All prerequisites met"
echo ""

# Create necessary directories
echo "📁 Creating project directories..."
mkdir -p backend/app backend/services backend/models
mkdir -p frontend/app frontend/components frontend/lib
mkdir -p scripts monitoring/dashboards
mkdir -p data/models data/documents data/cache

# Create development .env file
echo "📝 Creating development environment file..."
cat > .env.dev << EOF
# Development Environment Configuration
NODE_ENV=development

# Single GPU Configuration
GPU_COUNT=1
GPU_MEMORY_GB=32
GPU_MODEL=RTX_5090

# Model Configuration for 32GB VRAM
# Can run multiple models simultaneously
PRIMARY_MODELS=llama3.1:8b,mistral:7b,codellama:13b
THERAPEUTIC_MODEL=safespace:7b
MAX_LOADED_MODELS=4

# Service URLs (Docker internal)
DATABASE_URL=postgresql://jarvis_user:jarvis_dev_pass@postgres:5432/jarvis
REDIS_URL=redis://redis:6379
MILVUS_HOST=milvus
OLLAMA_HOST=http://ollama:11434
RABBITMQ_URL=amqp://jarvis:jarvis_dev@rabbitmq:5672/jarvis

# Development Secrets (NOT FOR PRODUCTION)
JWT_SECRET=dev_secret_key_for_local_development_only
NEXTAUTH_SECRET=dev_nextauth_secret_change_in_production

# Development OAuth (optional)
GOOGLE_CLIENT_ID=your-dev-google-client-id
GOOGLE_CLIENT_SECRET=your-dev-google-client-secret

# MinIO Development
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# Development Ports
API_PORT=8000
FRONTEND_PORT=3000
OLLAMA_PORT=11434
MILVUS_PORT=19530
POSTGRES_PORT=5432
REDIS_PORT=6379
RABBITMQ_PORT=5672
RABBITMQ_MGMT_PORT=15672
GRAFANA_PORT=3001
PROMETHEUS_PORT=9090
EOF

# Create model preload script
echo "📝 Creating model preload script..."
cat > scripts/preload-dev-models.sh << 'EOF'
#!/bin/bash
# Preload essential models for development

echo "🤖 Preloading models for RTX 5090 (32GB)..."
echo "This will download and cache models locally"
echo ""

# Essential models that fit well in 32GB
models=(
    "llama3.1:8b"      # 8.5GB - General purpose
    "mistral:7b"       # 7.5GB - Fast inference
    "codellama:13b"    # 13.5GB - Code generation
    "safespace:7b"     # 7.5GB - Therapeutic mode
)

# Total: ~37GB but only ~30GB will be in VRAM at once

for model in "${models[@]}"; do
    echo "📥 Pulling $model..."
    docker compose -f docker-compose.dev.yml exec ollama ollama pull $model
done

echo ""
echo "✅ Models preloaded successfully!"
echo "💡 The system will automatically manage GPU memory"
echo "   by loading/unloading models as needed"
EOF

chmod +x scripts/preload-dev-models.sh

# Create development startup script
echo "📝 Creating development startup script..."
cat > scripts/start-dev.sh << 'EOF'
#!/bin/bash
# Start development environment

echo "🚀 Starting JarvisAI Development Environment..."
echo ""

# Use development compose file
export COMPOSE_FILE=docker-compose.dev.yml

# Start core services first
echo "🔧 Starting core services..."
docker compose up -d postgres redis minio etcd rabbitmq

# Wait for services to be ready
echo "⏳ Waiting for services to initialize..."
sleep 10

# Start AI services
echo "🤖 Starting AI services..."
docker compose up -d milvus ollama

# Wait for Ollama
echo "⏳ Waiting for Ollama to be ready..."
until docker compose exec ollama curl -f http://localhost:11434/api/tags > /dev/null 2>&1; do
    sleep 2
done

# Start application services
echo "🌐 Starting application services..."
docker compose up -d api frontend

# Start monitoring
echo "📊 Starting monitoring services..."
docker compose up -d prometheus grafana nvidia-gpu-exporter

echo ""
echo "✅ Development environment started!"
echo ""
echo "🌐 Access URLs:"
echo "   Frontend:  http://localhost:3000"
echo "   API:       http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo "   Grafana:   http://localhost:3001 (admin/admin)"
echo "   RabbitMQ:  http://localhost:15672 (jarvis/jarvis_dev)"
echo ""
echo "📊 GPU Memory Usage:"
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits
echo ""
echo "💡 Run 'docker compose -f docker-compose.dev.yml logs -f' to see logs"
EOF

chmod +x scripts/start-dev.sh

# Create GPU monitoring script
echo "📝 Creating GPU monitoring script..."
cat > scripts/monitor-gpu.sh << 'EOF'
#!/bin/bash
# Monitor GPU usage during development

while true; do
    clear
    echo "🖥️  RTX 5090 GPU Monitor"
    echo "======================="
    echo ""
    
    # Show GPU stats
    nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits | \
    awk -F', ' '{
        printf "GPU Util: %3d%%  |  VRAM: %5.1f / %5.1f GB  |  Temp: %d°C\n", 
        $1, $2/1024, $3/1024, $4
    }'
    
    echo ""
    echo "📊 Loaded Models:"
    
    # Check Ollama for loaded models
    if docker compose -f docker-compose.dev.yml exec ollama curl -s http://localhost:11434/api/tags 2>/dev/null | jq -r '.models[]?.name' 2>/dev/null; then
        :
    else
        echo "   (Ollama not ready)"
    fi
    
    echo ""
    echo "Press Ctrl+C to exit"
    sleep 2
done
EOF

chmod +x scripts/monitor-gpu.sh

# Create README for development
echo "📝 Creating development README..."
cat > README_DEV.md << 'EOF'
# JarvisAI Development Environment

## System Requirements Met ✅
- **GPU**: NVIDIA RTX 5090 (32GB VRAM)
- **Docker**: Installed with NVIDIA Container Toolkit
- **OS**: Linux with NVIDIA drivers

## Quick Start

1. **Start the development environment:**
   ```bash
   ./scripts/start-dev.sh
   ```

2. **Preload AI models (first time only):**
   ```bash
   ./scripts/preload-dev-models.sh
   ```

3. **Monitor GPU usage:**
   ```bash
   ./scripts/monitor-gpu.sh
   ```

## Development Workflow

### Single GPU Optimizations
The RTX 5090 with 32GB VRAM is excellent for development:
- Can run 3-4 models simultaneously
- Smart model loading/unloading
- No need for dual GPU complexity in dev

### Model Recommendations for 32GB VRAM
- **Primary Stack** (can run simultaneously):
  - llama3.1:8b (8.5GB) - General chat
  - codellama:13b (13.5GB) - Code generation
  - mistral:7b (7.5GB) - Fast responses
  - Total: ~30GB (leaves 2GB buffer)

- **Alternative Models** (swap as needed):
  - deepseek-r1:14b (14.5GB) - Advanced coding
  - qwen2.5:14b (14.5GB) - Multilingual
  - safespace:7b (7.5GB) - Therapeutic mode

### Architecture Differences from Production
1. **Single Ollama Instance**: Instead of dual GPU setup
2. **Automatic Model Management**: Smart loading/unloading
3. **Higher Model Concurrency**: 32GB allows more models
4. **Simplified Networking**: Single GPU = simpler routing

### Development Tips
1. The system automatically manages GPU memory
2. Models are loaded on-demand and cached
3. Least recently used models are unloaded when needed
4. Monitor GPU usage to optimize model selection

### Endpoints
- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Grafana**: http://localhost:3001
- **RabbitMQ**: http://localhost:15672

### Common Commands
```bash
# View logs
docker compose -f docker-compose.dev.yml logs -f

# Restart services
docker compose -f docker-compose.dev.yml restart api

# Load a new model
docker compose -f docker-compose.dev.yml exec ollama ollama pull model_name

# Check GPU memory
nvidia-smi

# Stop everything
docker compose -f docker-compose.dev.yml down
```
EOF

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Review the configuration in docker-compose.dev.yml"
echo "2. Start the environment: ./scripts/start-dev.sh"
echo "3. Preload models: ./scripts/preload-dev-models.sh"
echo "4. Monitor GPU: ./scripts/monitor-gpu.sh"
echo ""
echo "💡 Your RTX 5090 with 32GB VRAM is perfect for development!"
echo "   You can run multiple large models simultaneously."