# Jarvis AI: Advanced Bilingual AI Assistant

Jarvis is an advanced AI assistant system designed to function as a highly capable, bilingual assistant proficient in both English and Dutch. It is designed to handle complex query processing, offer technical assistance, engage in creative tasks, and provide everyday support.

## Key Features

- **Bilingual Support**: Automatically detects and responds in English or Dutch with natural fluency
- **Long-Term Memory**: Remembers past interactions and user-provided knowledge
- **Extended Context**: Handles substantial amounts of information within a single conversation
- **Internet-Verified Accuracy**: Verifies factual information using real-time internet searches with source citations
- **Comprehensive Knowledge Domains**: Expertise spans technology, science, humanities, daily tasks, and local knowledge

## Quick Start Guide

### Prerequisites

- **Docker**: Ensure Docker and Docker Compose are installed on your system
- For GPU acceleration: NVIDIA drivers and NVIDIA Container Toolkit installed

### Starting Jarvis AI (One-Click Setup)

#### Windows:

1. Right-click on `start.ps1` and select "Run with PowerShell" or open PowerShell and run:
   ```powershell
   .\start.ps1
   ```

#### Linux (Ubuntu):

1. Make the start script executable and run it:
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

### Accessing Jarvis

Once the startup script completes:
1. Open your browser and navigate to: http://localhost:3000
2. In the Open-WebUI interface, select the "jarvis" model from the model selector
3. Start chatting with Jarvis!

### Adding Knowledge to Jarvis

To expand Jarvis's knowledge with your documents:
1. In the Open-WebUI interface, navigate to the RAG (Retrieval-Augmented Generation) section
2. Create a new collection (e.g., "Jarvis Knowledge Base")
3. Upload your documents (PDF, TXT, DOCX, etc.)
4. Enable the collection for your conversations

## System Architecture

Jarvis runs as a set of interconnected Docker containers:

1. **Ollama**: Hosts the large language model with the Jarvis system prompt
2. **Open-WebUI**: Provides the web interface for interacting with Jarvis
3. **Jarvis Backend**: Python backend handling core Jarvis functionality
4. **ChromaDB**: Vector database for document storage and retrieval

All components are containerized, meaning you don't need to install anything directly on your system beyond Docker.

## Advanced Configuration

### Modifying System Resources

To adjust the resources allocated to Jarvis, edit the `docker-compose.yml` file:

```yaml
# Example: Adjust GPU allocation for Ollama
services:
  ollama:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1  # Adjust number of GPUs
              capabilities: [gpu]
```

### Changing Model Parameters

To modify the LLM parameters, edit the modelfile section in the start script (start.sh or start.ps1):

```
PARAMETER temperature 0.7  # Adjust creativity level
PARAMETER top_p 0.9        # Adjust response diversity
```

### Persistent Storage

All data is stored in the following directories, which persist between restarts:

- `./ollama-models`: LLM model files
- `./open-webui-data`: Web interface data and settings
- `./jarvis-data`: Jarvis backend data
- `./chroma-data`: Vector database storage

## Development and Customization

### Project Structure

```
JarvisAI/
├── src/                   # Python backend code
│   ├── core/              # Core system components
│   ├── knowledge/         # Knowledge retrieval and verification
│   ├── language/          # Language processing
│   ├── memory/            # Memory management
│   └── main.py            # Main entry point
├── docker-compose.yml     # Container orchestration
├── Dockerfile             # Python backend container
├── start.sh               # Linux startup script
├── start.ps1              # Windows startup script
└── README.md
```

### Customizing the Backend

To modify the Python backend functionality:
1. Edit the relevant files in the `src/` directory
2. Rebuild the container with: `docker compose build jarvis-backend`
3. Restart the system: `docker compose up -d`

## System Prompt

Jarvis uses the following system prompt to define its behavior and capabilities:

```
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
```

## Troubleshooting

### Common Issues

1. **Ollama fails to start**:
   - Ensure you have enough disk space
   - For GPU usage, verify NVIDIA drivers and Container Toolkit are properly installed

2. **Web interface not accessible**:
   - Check if containers are running: `docker ps`
   - Verify port 3000 is not in use by another application

3. **Model download taking too long**:
   - The first startup downloads the large language model (~10GB)
   - This is a one-time process; subsequent starts will be much faster

### Logs and Debugging

To view logs for any component:
```bash
# View logs for a specific service
docker logs jarvis-ollama
docker logs jarvis-webui

# Follow logs in real-time
docker logs -f jarvis-backend
```

## Credits

This project was developed by the JarvisAI team and contributors at [anubissbe/JarvisAI](https://github.com/anubissbe/JarvisAI).

The system prompt and architectural design draws inspiration from advanced LLM systems while focusing specifically on bilingual capabilities and knowledge integration.

## License

This project is licensed under the MIT License - see the LICENSE file for details.