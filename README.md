# Jarvis AI 3.0: Advanced Bilingual AI Assistant

A sophisticated AI assistant system with long-term memory, bilingual capabilities (English/Dutch), and advanced knowledge integration.

## Quick Start Guide

### Prerequisites

1. **Hardware Requirements**
   - Minimum 16GB RAM
   - NVIDIA GPU with 8GB VRAM (recommended)
   - 50GB free disk space

2. **Software Requirements**
   - Docker and Docker Compose
   - NVIDIA Container Toolkit (for GPU support)
   - Git

## Initial Setup

1. **Clone the Repositories**
   ```bash
   # Clone Jarvis AI
   git clone https://github.com/anubissbe/JarvisAI.git
   cd JarvisAI

   # The repository includes a modified version of Open WebUI
   cd open-webui
   ```

2. **Build Open WebUI Container**
   ```bash
   # Build the modified Open WebUI container
   cd open-webui
   docker build -t jarvis-webui .

   # This custom build includes:
   # - Memory system integration
   # - WebSocket handlers
   # - UI components
   # - Memory management
   ```

3. **Configure Environment**
   ```bash
   # Create .env file in JarvisAI root
   cat > .env << EOL
   JARVIS_API_KEY=your_secret_key_here
   MEMORY_RETENTION_DAYS=365
   MEMORY_ARCHIVE_DAYS=730
   MEMORY_IMPORTANCE_THRESHOLD=0.5
   DEBUG=false
   EOL

   # Create .env file in open-webui directory
   cat > open-webui/.env << EOL
   OLLAMA_API_BASE_URL=http://ollama:11434/api
   MEMORY_ENABLED=true
   MEMORY_WEBSOCKET_URL=ws://jarvis-backend:5000/ws
   EOL
   ```

4. **Start the System**
   - Windows:
     ```powershell
     # Right-click start.ps1 and select "Run with PowerShell"
     # OR open PowerShell and run:
     .\start.ps1
     ```
   
   - Linux:
     ```bash
     chmod +x start.sh
     ./start.sh
     ```

   The startup script will:
   1. Build the custom Open WebUI container
   2. Start all services with proper configuration
   3. Initialize the memory system
   4. Set up WebSocket connections

4. **Initial Configuration**
   - Open http://localhost:3000 in your browser
   - Log in with default credentials:
     - Username: admin
     - Password: admin
   - Change the default password immediately

### First-Time Setup Tasks

1. **Select Jarvis Model**
   - In Open WebUI, go to "Models" tab
   - Select "jarvis" from the model list
   - Wait for model download (~10GB)

2. **Create Knowledge Base**
   - Go to "RAG" (Retrieval-Augmented Generation) section
   - Create new collection: "Jarvis Knowledge Base"
   - Enable the collection

3. **Add Initial Knowledge**
   - Upload relevant documents to the knowledge base
   - Supported formats: PDF, TXT, DOCX, HTML
   - Documents are automatically processed and integrated

## System Components

### 1. Ollama (LLM Service)
- Hosts the Jarvis model
- Handles inference
- GPU acceleration

**Status Check:**
```bash
docker logs jarvis-ollama
# Should show model loaded and ready
```

### 2. Open WebUI
- Main user interface
- Document upload
- Chat interface
- Knowledge management

**Access:** http://localhost:3000

### 3. ChromaDB
- Vector database
- Knowledge storage
- Semantic search

**Health Check:**
```bash
curl http://localhost:8000/api/v1/heartbeat
```

### 4. Jarvis Backend
- Memory management
- Knowledge integration
- Language detection
- WebSocket server

**Health Check:**
```bash
curl http://localhost:5000/health
```

## Memory System Integration

The memory system is deeply integrated with Open WebUI to provide seamless long-term memory and context awareness.

### Components

1. **Backend Integration** (`open-webui/backend/open_webui/`)
   - `models/memory.py`: Memory data models
   - `routers/memory.py`: Memory API endpoints
   - `socket/memory.py`: WebSocket handlers for real-time memory sync

2. **Frontend Integration** (`open-webui/src/lib/`)
   - `stores/memory.ts`: Memory state management
   - `components/memory/`: Memory UI components

### Storage Tiers

1. **Active Memory** (1 year)
   - Recent conversations
   - Frequently accessed information
   - Path: `./data/memory/active/`
   ```yaml
   retention:
     days: 365
     max_size: "10GB"
     compression: true
   ```

2. **Archive** (2 years)
   - Older conversations
   - Less accessed information
   - Path: `./data/memory/archive/`
   ```yaml
   retention:
     days: 730
     max_size: "50GB"
     compression: true
   ```

3. **Important Memory** (Indefinite)
   - Critical information
   - High-importance conversations
   - Path: `./data/memory/important/`
   ```yaml
   retention:
     days: -1  # Indefinite
     max_size: "100GB"
     compression: true
   ```

### Memory Features

1. **Real-time Synchronization**
   - WebSocket-based memory updates
   - Automatic conversation capture
   - Context preservation
   ```typescript
   // Subscribe to memory updates
   memoryStore.subscribe((state) => {
     console.log('Memory updated:', state);
   });
   ```

2. **Importance Scoring**
   - Automatic scoring based on:
     - Topic relevance (30%)
     - Reference count (25%)
     - Interaction depth (25%)
     - Recency of references (20%)
   ```python
   importance_score = (
     topic_relevance * 0.3 +
     reference_count * 0.25 +
     interaction_depth * 0.25 +
     recency_score * 0.2
   )
   ```

3. **Context Integration**
   - Automatic context retrieval
   - Related conversation linking
   - Knowledge graph integration

### UI Components

1. **Memory Manager**
   ```svelte
   <script>
     import { MemoryManager } from '$lib/components/memory';
   </script>

   <MemoryManager conversationId={currentChat.id} />
   ```

2. **Memory Stats**
   ```svelte
   <script>
     import { memoryStats } from '$lib/stores/memory';
   </script>

   <div>
     Total Memories: {$memoryStats.total}
     Important: {$memoryStats.important}
     Archived: {$memoryStats.archived}
   </div>
   ```

### API Endpoints

1. **Memory Management**
   ```bash
   # Get memory stats
   GET /api/v1/memory/stats

   # Get conversation memories
   GET /api/v1/memory/conversations/{conversation_id}

   # Store new memory
   POST /api/v1/memory/conversations/{conversation_id}

   # Search memories
   GET /api/v1/memory/search?query=example

   # Cleanup memories
   POST /api/v1/memory/cleanup
   ```

2. **WebSocket Events**
   ```javascript
   // Memory update event
   {
     type: 'memory_update',
     conversation_id: 'conv123',
     memory: {
       id: 'mem123',
       content: '...',
       importance: 0.8
     }
   }

   // Sync response event
   {
     type: 'sync_response',
     conversation_id: 'conv123',
     memories: [...]
   }
   ```

### Configuration

1. **Memory Settings** (`docker-compose.yml`)
   ```yaml
   jarvis-backend:
     environment:
       MEMORY_RETENTION_DAYS: 365
       MEMORY_ARCHIVE_DAYS: 730
       MEMORY_IMPORTANCE_THRESHOLD: 0.5
       MAX_CONVERSATION_HISTORY: 1000
   ```

2. **UI Configuration** (`webui-config.json`)
   ```json
   {
     "memory": {
       "enabled": true,
       "autoSync": true,
       "syncInterval": 300,
       "showStats": true
     }
   }
   ```

### Usage Examples

1. **Enable Memory in Chat**
   ```svelte
   <Chat
     conversationId={currentChat.id}
     enableMemory={true}
     memoryOptions={{
       autoSync: true,
       importanceThreshold: 0.5
     }}
   />
   ```

2. **Manual Memory Operations**
   ```typescript
   // Store memory
   await memoryStore.storeMemory({
     conversation_id: 'conv123',
     user_message: 'Hello',
     assistant_message: 'Hi there',
     context: { /* ... */ }
   });

   // Sync conversation
   await memoryStore.syncConversation('conv123');

   // Clear conversation memory
   await memoryStore.clearConversation('conv123');
   ```

3. **Access Memory Context**
   ```typescript
   // Get active memories
   const memories = get(activeMemories);

   // Get memory stats
   const stats = get(memoryStats);

   // Check connection status
   const { connected, error } = get(connectionStatus);
   ```

### Adding Knowledge

1. **Through Web Interface**
   ```
   1. Open http://localhost:3000
   2. Go to RAG section
   3. Upload documents
   4. Documents are automatically processed and integrated with memory
   ```

2. **Through API**
   ```bash
   # Upload document
   curl -X POST http://localhost:5000/upload-knowledge \
        -H "Content-Type: multipart/form-data" \
        -F "file=@your_document.pdf"

   # Get document status
   curl http://localhost:5000/api/v1/knowledge/status/{doc_id}
   ```

### Monitoring

1. **Memory Metrics**
   ```bash
   # Get memory stats
   curl http://localhost:5000/api/v1/memory/stats

   # Get WebSocket metrics
   curl http://localhost:5000/metrics/websocket
   ```

2. **UI Monitoring**
   - Memory usage indicators
   - Connection status
   - Sync status
   - Importance distribution

### Troubleshooting

1. **Memory Sync Issues**
   ```bash
   # Check WebSocket status
   curl http://localhost:5000/metrics/websocket

   # Force memory sync
   curl -X POST http://localhost:5000/api/v1/memory/sync \
        -H "Content-Type: application/json" \
        -d '{"conversation_id": "conv123"}'
   ```

2. **Memory Storage Issues**
   ```bash
   # Check storage usage
   curl http://localhost:5000/api/v1/memory/storage

   # Trigger cleanup
   curl -X POST http://localhost:5000/api/v1/memory/cleanup
   ```

## Maintenance Tasks

### Regular Maintenance

1. **Backup Data**
   ```bash
   # Stop services
   docker compose down

   # Backup volumes
   tar -czf jarvis_backup_$(date +%Y%m%d).tar.gz \
       ./data/memory \
       ./data/knowledge \
       ./chroma-data

   # Restart services
   docker compose up -d
   ```

2. **Update System**
   ```bash
   git pull
   docker compose pull
   docker compose up -d
   ```

3. **Clean Old Data**
   ```bash
   # Automatic cleanup runs daily
   # Force cleanup:
   curl -X POST http://localhost:5000/api/v1/memory/cleanup
   ```

### Monitoring

1. **View Logs**
   ```bash
   # All services
   docker compose logs -f

   # Specific service
   docker logs jarvis-ollama
   docker logs jarvis-webui
   docker logs jarvis-backend
   ```

2. **Check Memory Usage**
   ```bash
   curl http://localhost:5000/api/v1/memory/stats
   ```

3. **Monitor WebSocket**
   ```bash
   curl http://localhost:5000/metrics/websocket
   ```

## Troubleshooting

### Common Issues

1. **GPU Not Detected**
   ```bash
   # Check NVIDIA drivers
   nvidia-smi
   
   # Verify Docker GPU support
   docker run --gpus all nvidia/cuda:11.0-base nvidia-smi
   ```

2. **Memory System Issues**
   - Check disk space: `df -h`
   - Verify permissions: `ls -l ./data/memory/`
   - Check logs: `docker logs jarvis-backend`

3. **WebUI Not Responding**
   ```bash
   # Check if containers are running
   docker ps
   
   # Restart WebUI
   docker compose restart webui
   ```

4. **Knowledge Base Issues**
   ```bash
   # Reset ChromaDB
   docker compose down
   rm -rf ./chroma-data/*
   docker compose up -d
   ```

### Advanced Configuration

1. **Memory Settings** (docker-compose.yml)
   ```yaml
   jarvis-backend:
     environment:
       MEMORY_RETENTION_DAYS: 365
       MEMORY_ARCHIVE_DAYS: 730
       MAX_CONVERSATION_HISTORY: 1000
       MEMORY_IMPORTANCE_THRESHOLD: 0.5
   ```

2. **Resource Allocation**
   ```yaml
   services:
     ollama:
       deploy:
         resources:
           limits:
             memory: 8G
             cpus: '4'
   ```

3. **Network Configuration**
   ```yaml
   services:
     jarvis-backend:
       ports:
         - "5000:5000"
       networks:
         - jarvis_net
   ```

## Security Considerations

1. **API Key**
   - Change default API key in .env file
   - Use strong, random key
   - Rotate regularly

2. **Network Security**
   - Use HTTPS in production
   - Configure firewalls
   - Limit access to necessary ports

3. **Data Protection**
   - Regular backups
   - Encryption at rest
   - Access control

## Upgrading

1. **Backup Current System**
   ```bash
   ./scripts/backup.sh
   ```

2. **Update Code**
   ```bash
   git pull origin main
   ```

3. **Update Containers**
   ```bash
   docker compose pull
   docker compose up -d
   ```

4. **Verify Update**
   ```bash
   # Check version
   curl http://localhost:5000/version

   # Check health
   curl http://localhost:5000/health
   ```

## Support and Community

- GitHub Issues: [Report bugs](https://github.com/anubissbe/JarvisAI/issues)
- Discord: [Join community](https://discord.gg/jarvisai)
- Documentation: [Full docs](https://docs.jarvisai.com)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Getting Help

If you encounter any issues or need assistance:

1. Check the troubleshooting section above
2. Search existing GitHub issues
3. Join our Discord community
4. Open a new GitHub issue with:
   - System information
   - Error messages
   - Steps to reproduce
   - Logs (if applicable)

## Contributing

We welcome contributions! Please see CONTRIBUTING.md for details on:
- Code style
- Pull request process
- Development setup
- Testing requirements