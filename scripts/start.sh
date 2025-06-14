#!/bin/bash

# JarvisAI Startup Script
# Comprehensive startup and initialization script

set -e

echo "🚀 Starting JarvisAI Self-Hosted AI Assistant"
echo "=============================================="

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found. Please run this script from the JarvisAI root directory."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration before starting services."
    echo "   Especially configure passwords and API keys."
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Check if nvidia-docker is available (for GPU support)
if command -v nvidia-docker > /dev/null 2>&1; then
    echo "✅ NVIDIA Docker support detected"
else
    echo "⚠️  NVIDIA Docker not found - GPU acceleration will not be available"
fi

echo "🐳 Building and starting Docker services..."

# Build custom images first
echo "📦 Building custom images..."
docker-compose build

# Start core infrastructure services first
echo "🗄️  Starting core infrastructure..."
docker-compose up -d postgres redis qdrant minio

# Wait for services to be ready
echo "⏳ Waiting for core services to be ready..."
sleep 10

# Check if PostgreSQL is ready
echo "🔍 Checking PostgreSQL connection..."
for i in {1..30}; do
    if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
        echo "✅ PostgreSQL is ready"
        break
    fi
    echo "   Waiting for PostgreSQL... ($i/30)"
    sleep 2
done

# Check if Redis is ready
echo "🔍 Checking Redis connection..."
for i in {1..30}; do
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis is ready"
        break
    fi
    echo "   Waiting for Redis... ($i/30)"
    sleep 2
done

# Start Ollama service
echo "🤖 Starting Ollama LLM service..."
docker-compose up -d ollama

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to be ready..."
sleep 15

for i in {1..60}; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama is ready"
        break
    fi
    echo "   Waiting for Ollama... ($i/60)"
    sleep 3
done

# Start API and application services
echo "🌐 Starting API and application services..."
docker-compose up -d api document-processor agent-orchestrator

# Start frontend
echo "🎨 Starting frontend interface..."
docker-compose up -d frontend

# Start monitoring (optional)
echo "📊 Starting monitoring services..."
docker-compose up -d prometheus grafana

# Final status check
echo ""
echo "🎯 Checking service status..."
docker-compose ps

echo ""
echo "✅ JarvisAI startup complete!"
echo ""
echo "🌐 Access Points:"
echo "   • JarvisAI Chat Interface: http://localhost:3000"
echo "   • API Documentation: http://localhost:8000/docs"
echo "   • Grafana Monitoring: http://localhost:3001 (admin/admin)"
echo "   • MinIO Console: http://localhost:9001"
echo "   • Prometheus: http://localhost:9090"
echo ""
echo "📋 Next Steps:"
echo "   1. Access the chat interface at http://localhost:3000"
echo "   2. Configure OAuth providers in .env if needed"
echo "   3. Pull AI models: ./scripts/setup-models.sh"
echo "   4. Upload documents via the web interface"
echo ""
echo "📖 Documentation: See README.md for detailed usage instructions"
echo "🛠️  Logs: docker-compose logs -f [service-name]"
echo "⏹️  Stop: docker-compose down"