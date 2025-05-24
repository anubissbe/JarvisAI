# Stop any running containers and clean up
Write-Host "Cleaning up existing containers and volumes..."
docker-compose down --volumes
docker rm -f jarvis-ollama jarvis-webui jarvis-chromadb jarvis-backend 2>$null
docker volume rm jarvisai-30_ollama_data jarvisai-30_webui_data jarvisai-30_chroma_data jarvisai-30_backend_data 2>$null
docker network prune -f

# Start Ollama container first
Write-Host "Starting Ollama container..."
docker-compose up -d ollama

# Wait for Ollama to be ready
Write-Host "Waiting for Ollama to be ready..."
$ready = $false
$attempts = 0
$maxAttempts = 30

while (-not $ready -and $attempts -lt $maxAttempts) {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -ErrorAction SilentlyContinue
        if ($response) {
            $ready = $true
            Write-Host "Ollama is ready!"
        }
    }
    catch {
        Start-Sleep -Seconds 2
        $attempts++
        Write-Host "Waiting for Ollama... (Attempt $attempts/$maxAttempts)"
    }
}

if (-not $ready) {
    Write-Host "Error: Ollama failed to start after $maxAttempts attempts"
    exit 1
}

# Pull Mistral model
Write-Host "Pulling Mistral model..."
docker exec jarvis-ollama ollama pull mistral:latest

# Create Jarvis model
Write-Host "Creating Jarvis model..."
$modelfile = @"
FROM mistral:latest
PARAMETER temperature 0.7
PARAMETER top_p 0.9
SYSTEM you are a bilingual AI assistant with English and Dutch capabilities
"@

Write-Host "Creating modelfile..."
$modelfile | Out-File -FilePath "modelfile" -Encoding utf8 -NoNewline

Write-Host "Copying modelfile to container..."
docker cp modelfile jarvis-ollama:/root/.ollama/modelfile

Write-Host "Creating model in Ollama..."
docker exec jarvis-ollama sh -c 'cd /root/.ollama && ollama create jarvis -f modelfile'

# Start remaining services
Write-Host "Starting remaining services..."
docker-compose up -d

Write-Host "`nJarvis AI is now starting up!"
Write-Host "Once the services are ready, you can access:"
Write-Host "- Web interface: http://localhost:3000"
Write-Host "- Backend API: http://localhost:5000"
Write-Host "- ChromaDB: http://localhost:8000"
Write-Host "`nSelect the 'jarvis' model in the web interface to begin chatting!"