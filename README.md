# JarvisAI - Self-Hosted RAG System with Knowledge Graph

JarvisAI is an advanced bilingual AI assistant with expertise in both English and Dutch, featuring a self-hosted Retrieval-Augmented Generation (RAG) system with knowledge graph capabilities.

## Features

- **Bilingual Support**: Automatically detects and responds in English or Dutch
- **Knowledge Graph**: Uses Neo4j to store and query relationships between concepts
- **Vector Search**: Employs Milvus for semantic similarity search
- **Document Processing**: Automatically extracts knowledge from uploaded documents
- **Hybrid Search**: Combines graph-based and vector-based search for comprehensive results
- **Personal Knowledge Management**: Extracts and organizes personal information

## System Components

- **Ollama**: Serves the LLM (Llama 3.1 8B)
- **Neo4j**: Graph database for knowledge storage
- **Milvus**: Vector database for semantic search
- **OpenWebUI**: Web interface for interacting with the system
- **Document Processor**: Processes and indexes uploaded documents
- **Ollama Proxy**: Augments queries with knowledge from the RAG system

## Getting Started

1. Run the `start.sh` script to set up and launch JarvisAI:
   ```bash
   ./start.sh
   ```

2. Access the web interface at http://localhost:3000

3. Upload documents to your knowledge base through the web interface

4. Chat with Jarvis using the web interface

## Environment Variables

Key environment variables are stored in `jarvis_kb_config.env`. You can modify these to customize your deployment.

## System Requirements

- Docker and Docker Compose
- 16GB+ RAM recommended
- NVIDIA GPU recommended (but optional)
- 20GB+ free disk space

## Troubleshooting

If you encounter issues:
- Check the logs with `docker-compose logs -f [service-name]`
- Ensure all services are running with `docker-compose ps`
- Verify that the Jarvis model is available with `curl http://localhost:11434/api/tags`

## License

This project is open source and available under the MIT License.