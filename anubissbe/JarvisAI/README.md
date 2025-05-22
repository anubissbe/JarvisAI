# ... existing code ...

## Features

- 🤖 Conversational AI powered by Ollama models
- 🔊 Text-to-speech capabilities for natural interaction
- 🎛️ Customizable settings for voice, AI model, and appearance
- 🔌 Extensible integration system for third-party services
- 🔒 User authentication and personalized experiences
- 📱 Responsive design that works on desktop and mobile
- 📚 Knowledge base for uploading and querying documents

# ... existing code ...

### Required Configuration

After installation, you'll need to configure the following:

1. **Ollama Setup**: JarvisAI uses Ollama for AI functionality. The docker-compose file includes Ollama, but you may need to pull models:
   ```bash
   docker exec -it jarvisai-ollama-1 ollama pull llama3
   docker exec -it jarvisai-ollama-1 ollama pull nomic-embed-text-v1.5
   ```

# ... existing code ...