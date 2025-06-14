#!/bin/bash

# JarvisAI Model Setup Script
# Download and configure recommended AI models

set -e

echo "🤖 JarvisAI Model Setup"
echo "======================"

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "❌ Error: Ollama is not running. Please start JarvisAI first with ./scripts/start.sh"
    exit 1
fi

echo "📥 Downloading recommended AI models..."
echo "⚠️  Note: This will download several GB of data and may take a while."
echo ""

# Function to pull model with progress
pull_model() {
    local model=$1
    local description=$2
    
    echo "📦 Pulling $model ($description)..."
    if docker-compose exec ollama ollama pull "$model"; then
        echo "✅ $model downloaded successfully"
    else
        echo "❌ Failed to download $model"
        return 1
    fi
    echo ""
}

# Pull core models
echo "🎯 Core Models (Recommended for all users):"
echo ""

pull_model "llama3.1:8b" "General conversation and reasoning"
pull_model "mistral:7b" "Fast, efficient responses"

echo "🔧 Specialized Models:"
echo ""

# Ask user if they want coding models
read -p "📝 Download CodeLlama 13B for programming tasks? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    pull_model "codellama:13b" "Programming and code generation"
fi

# Ask user if they want larger models
read -p "🧠 Download DeepSeek-R1 14B for advanced reasoning? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    pull_model "deepseek-r1:14b" "Advanced reasoning and problem-solving"
fi

# Ask user if they want multilingual models
read -p "🌍 Download Qwen2.5 7B for multilingual support? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    pull_model "qwen2.5:7b" "Multilingual support"
fi

echo "📊 Checking available models..."
echo ""
docker-compose exec ollama ollama list

echo ""
echo "✅ Model setup complete!"
echo ""
echo "💡 Usage Tips:"
echo "   • Switch models in the web interface at http://localhost:3000"
echo "   • Use CodeLlama for programming questions"
echo "   • Use Mistral for quick responses"
echo "   • Use LLaMA 3.1 for detailed conversations"
echo ""
echo "🔧 Advanced Usage:"
echo "   • View model details: docker-compose exec ollama ollama show [model-name]"
echo "   • Remove models: docker-compose exec ollama ollama rm [model-name]"
echo "   • See all available models: docker-compose exec ollama ollama list"