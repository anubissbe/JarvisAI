Write-Host "Stopping JarvisAI containers..." -ForegroundColor Cyan
docker-compose down

Write-Host "Removing ChromaDB volume to ensure clean start..." -ForegroundColor Cyan
docker volume rm jarvisai-30_chroma_data -f

Write-Host "Building containers..." -ForegroundColor Cyan
docker-compose build chromadb

Write-Host "Starting JarvisAI containers..." -ForegroundColor Cyan
docker-compose up -d

Write-Host "JarvisAI containers have been restarted!" -ForegroundColor Green
Write-Host "You can view logs with: docker-compose logs -f" -ForegroundColor Yellow
Write-Host "To view logs without the 404 messages, use: docker-compose logs -f jarvis-backend jarvis-ollama jarvis-webui" -ForegroundColor Yellow