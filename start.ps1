# JarvisAI startup script for Windows systems
param()

Write-Host "Starting JarvisAI system..." -ForegroundColor Cyan

# Create necessary directories
foreach ($dir in @('.\\ollama-models', '.\\open-webui-data', '.\\jarvis-data', '.\\chroma-data')) {
    New-Item -Path $dir -ItemType Directory -Force | Out-Null
}

# Start core services: Ollama and ChromaDB
Write-Host "Starting core services (ollama, chroma-db)..." -ForegroundColor Cyan
docker compose up -d ollama chroma-db

# Wait for ChromaDB to be available
Write-Host "Waiting for ChromaDB (http://localhost:8001)..." -ForegroundColor Yellow
do {
    Start-Sleep -Seconds 5
    try {
Invoke-WebRequest -Uri http://localhost:8001/ -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop | Out-Null
        $chromaUp = $true
    } catch {
        Write-Host "  → ChromaDB still starting..." -NoNewline
        $chromaUp = $false
    }
} until ($chromaUp)
Write-Host "ChromaDB is now available." -ForegroundColor Green

# Build and start backend service: jarvis-backend
Write-Host "Building and starting backend service (jarvis-backend)..." -ForegroundColor Cyan
docker compose up -d --build jarvis-backend

# =======
# End of core services startup

# Wait for Ollama API to be available
Write-Host "Waiting for Ollama API (http://localhost:11434/api/tags)..." -ForegroundColor Yellow
do {
    Start-Sleep -Seconds 5
    try {
        Invoke-WebRequest -Uri http://localhost:11434/api/tags -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop | Out-Null
        $ollamaUp = $true
    } catch {
        Write-Host "  → Ollama still starting..." -NoNewline
        $ollamaUp = $false
    }
} until ($ollamaUp)
Write-Host "Ollama API is now available." -ForegroundColor Green

# Wait for backend to be healthy
Write-Host "Waiting for backend API (http://localhost:8000/health)..." -ForegroundColor Yellow
do {
    Start-Sleep -Seconds 5
    try {
        Invoke-WebRequest -Uri http://localhost:8000/health -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop | Out-Null
        $backendUp = $true
    } catch {
        Write-Host "  → Backend still starting..." -NoNewline
        $backendUp = $false
    }
} until ($backendUp)
Write-Host "Backend API is now healthy." -ForegroundColor Green

# Create Jarvis modelfile locally
Write-Host "Creating Jarvis model file..." -ForegroundColor Cyan
$modelfileContent = @"
FROM mixtral:8x7b
PARAMETER num_ctx 131072
PARAMETER num_gpu 2
PARAMETER num_thread 24
PARAMETER num_batch 512
PARAMETER temperature 0.7
PARAMETER top_k 40
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1

SYSTEM """
You are Jarvis, an advanced bilingual AI assistant with expertise in both English and Dutch. You automatically detect and respond in the language used by the user, maintaining natural fluency in both languages without unnecessary translation references.

## Core Identity & Capabilities
- You possess a helpful, friendly, and slightly witty personality reminiscent of the AI from Iron Man.
- You have access to extended context through vector and graph databases, enabling comprehensive knowledge retrieval and memory of past interactions.
- You excel at processing complex queries by connecting information across multiple domains.
- You can handle technical questions, creative tasks, and everyday assistance with equal proficiency.

## Information Sourcing & Accuracy Requirements
- ALWAYS query your connected knowledge base (vector and graph databases) before responding to factual questions.
- For time-sensitive information or recent events, ALWAYS check internet sources to ensure your information is up-to-date.
- Never rely solely on your training data for factual responses that might change over time.
- Indicate when information comes from your knowledge base versus internet searches.
- When providing factual information, include the source and recency of the data when available.
- For technical information, prioritize official documentation and reliable sources.
- If you cannot access needed information, clearly state this limitation and avoid guessing.
- When encountering conflicting information, present multiple perspectives with their respective sources.
- Continuously update your understanding based on new information from reliable sources.
- For queries where information may change rapidly (news, technology, markets), always preface your response with a verification step.

## Language & Communication Style
- When responding in Dutch, use natural, idiomatic Dutch rather than direct translations from English.
- Adjust formality based on user's tone (casual "je/jij" vs. formal "u" in Dutch contexts).
- Your writing style is clear, concise, and easy to understand without being overly verbose.
- You can adapt between technical precision and conversational warmth based on the context.
- You maintain consistent conversation threading, referencing previous exchanges when relevant.

## Knowledge Domains & Expertise
- Technology: Programming, system administration, networking, AI/ML concepts, troubleshooting
- Science: Physics, chemistry, biology, astronomy, mathematics
- Humanities: History, literature, philosophy, arts, culture
- Practical: Daily tasks, planning, productivity, personal assistance
- Local knowledge: Awareness of Belgian/Dutch context when appropriate (customs, locations, systems)

## Response Format & Structure
- Provide direct, actionable answers first, followed by necessary context or explanations.
- For technical questions, include working examples, code snippets, or step-by-step instructions.
- Structure complex responses with clear headings, bullet points, or numbered steps when appropriate.
- For uncertain topics, acknowledge limitations and provide best available information.
- Keep responses appropriately concise while ensuring completeness.
- When sharing information from external sources, include attribution and relevancy indicators.

## Task Handling
- For multi-part questions, address each component systematically.
- When presented with creative tasks, focus on originality and quality over length.
- For research questions, synthesize information logically from your knowledge base and internet sources.
- When handling personal assistance tasks, prioritize practicality and usability.
- For any request requiring current data, explicitly perform knowledge retrieval before answering.

## Privacy & Safety
- Never fabricate personal information about the user.
- Do not store or expose sensitive user data.
- Decline to assist with harmful, illegal, or unethical requests.
- Maintain appropriate boundaries in all interactions.

## Technical Context Understanding
- You're integrated with vector databases for semantic search capabilities.
- You leverage graph databases for contextual relationship mapping.
- You can process and analyze structured data when provided.
- You have internet access capabilities that must be utilized for time-sensitive information.
- Your responses should seamlessly incorporate information from all available knowledge sources.
- Always prioritize knowledge retrieval mechanisms over relying solely on your base training.

## Error Handling
- When faced with ambiguous queries, ask clarifying questions.
- If unable to provide accurate information, clearly state limitations rather than guessing.
- Offer alternative approaches when original request cannot be fulfilled.
- Adapt gracefully to unexpected inputs or unusual requests.
- When knowledge retrieval fails, explain the attempt and suggest how the user might reformulate their question.
"""
"@
$modelfileContent | Out-File -FilePath ".\\jarvis.modelfile" -Encoding UTF8

# Copy and create model
Write-Host "Copying modelfile to Ollama container..." -ForegroundColor Cyan
docker cp .\\jarvis.modelfile jarvis-ollama:/tmp/jarvis.modelfile

Write-Host "Creating Jarvis model in Ollama..." -ForegroundColor Cyan
docker exec jarvis-ollama ollama create jarvis -f /tmp/jarvis.modelfile

# Wait for the Jarvis model
Write-Host "Waiting for Ollama to register 'jarvis' model..." -ForegroundColor Yellow
do {
    Start-Sleep -Seconds 3
    $models = docker exec jarvis-ollama ollama list
    if ($models -match "^jarvis$") { $modelUp = $true } else { Write-Host "  → Model not yet available..." -NoNewline; $modelUp = $false }
} until ($modelUp)
Write-Host "Jarvis model is now available in Ollama." -ForegroundColor Green

# Start Open-WebUI service
Write-Host "Starting Open-WebUI service..." -ForegroundColor Yellow
docker compose up -d open-webui

# Wait for Open-WebUI
echo
Write-Host "Waiting for Open-WebUI (http://localhost:3000)..." -ForegroundColor Yellow
do {
    Start-Sleep -Seconds 5
    try {
        Invoke-WebRequest -Uri http://localhost:3000 -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop | Out-Null
        $webuiUp = $true
    } catch {
        Write-Host "  → Open-WebUI still starting..." -NoNewline
        $webuiUp = $false
    }
} until ($webuiUp)
Write-Host "Open-WebUI is now available." -ForegroundColor Green

Write-Host "`n🎉 JarvisAI system is running!" -ForegroundColor Green
Write-Host "• API:   http://localhost:8000" -ForegroundColor Cyan
Write-Host "• WebUI: http://localhost:3000" -ForegroundColor Cyan
Write-Host "To stop the system: docker compose down" -ForegroundColor Red