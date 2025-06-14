#!/bin/bash
# Development setup script for JarvisAI backend

echo "🚀 Setting up JarvisAI Backend Development Environment..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}📝 Creating .env file from template...${NC}"
    cp .env.example .env
    
    # Generate a secure secret key
    SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
    
    # Update .env with generated secret key
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
    else
        # Linux
        sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
    fi
    
    echo -e "${GREEN}✅ Generated secure SECRET_KEY${NC}"
fi

# Start infrastructure services
echo -e "${YELLOW}🐳 Starting infrastructure services...${NC}"
docker-compose -f ../docker-compose.dev.yml up -d

# Wait for services to be healthy
echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"

# Wait for PostgreSQL
until docker exec jarvis-postgres pg_isready -U jarvis > /dev/null 2>&1; do
    echo -n "."
    sleep 1
done
echo -e "\n${GREEN}✅ PostgreSQL is ready${NC}"

# Wait for Redis
until docker exec jarvis-redis redis-cli ping > /dev/null 2>&1; do
    echo -n "."
    sleep 1
done
echo -e "${GREEN}✅ Redis is ready${NC}"

# Check Python virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}🐍 Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}✅ Development environment setup complete!${NC}"
echo -e "\n${YELLOW}📋 Next steps:${NC}"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Run the application: uvicorn main:app --reload"
echo "3. Open API docs: http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}🔧 Useful commands:${NC}"
echo "- Check service status: docker-compose -f ../docker-compose.dev.yml ps"
echo "- View logs: docker-compose -f ../docker-compose.dev.yml logs -f"
echo "- Stop services: docker-compose -f ../docker-compose.dev.yml down"