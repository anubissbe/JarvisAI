# Script to rebuild and restart Jarvis AI backend with the fixes for deprecation warnings
Write-Host "Stopping and removing jarvis-backend container..." -ForegroundColor Yellow
docker-compose stop jarvis-backend
docker-compose rm -f jarvis-backend

Write-Host "Rebuilding jarvis-backend container with updated dependencies..." -ForegroundColor Yellow
docker-compose build jarvis-backend

Write-Host "Starting jarvis-backend container with the fixes..." -ForegroundColor Yellow
docker-compose up -d jarvis-backend

Write-Host "Following logs to verify the fixes..." -ForegroundColor Green
docker-compose logs -f jarvis-backend