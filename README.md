JarvisAI: Self-Hosted RAG System with Knowledge Graph
=====================================================

JarvisAI is a powerful self-hosted Retrieval-Augmented Generation (RAG) system that combines Large Language Models with a hybrid knowledge retrieval mechanism based on both graph databases (Neo4j) and vector databases (Milvus). This system enables advanced document processing, knowledge extraction, and intelligent context-aware AI responses.

**Note:** JarvisAI is designed to run on systems with NVIDIA GPUs (particularly V100) for optimal performance.

### 🚀 Quick Start

To get started with JarvisAI on a fresh Ubuntu 22.04 server, run:

    git clone https://github.com/AnubissBE/jarvisai.git
    cd jarvisai
    chmod +x start.sh
    ./start.sh

The `start.sh` script installs Docker if needed and launches all containers in one go. No additional configuration is required.



Table of Contents
-----------------

*   [Overview](#overview)
*   [Key Features](#features)
*   [System Components](#components)
*   [Architecture](#architecture)
*   [Requirements](#requirements)
*   [Installation](#installation)
*   [Configuration](#configuration)
*   [Usage](#usage)
*   [Document Processing](#document-processing)
*   [Knowledge Extraction](#knowledge-extraction)
*   [Troubleshooting](#troubleshooting)
*   [Security Notes](#security)
*   [Development](#development)

Overview
--------

JarvisAI is designed to enhance Large Language Models (LLMs) with a powerful combination of knowledge graph and vector search capabilities, allowing for more accurate, context-aware, and factual responses. The system processes documents, extracts both technical and personal knowledge, and builds a sophisticated knowledge graph that can be queried using both semantic and graph-based approaches.

Key capabilities include:

*   Processing various document formats (PDF, text files, code, etc.)
*   Extracting technical concepts, topics, and relationships from documents
*   Identifying personal information, entities, and relationships within documents
*   Building a knowledge graph in Neo4j and vector representations in Milvus
*   Providing hybrid search that combines graph traversal with semantic similarity
*   Enhancing LLM responses with relevant context from your knowledge base
*   Bilingual support for both English and Dutch

Key Features
------------

### Document Processing

*   Support for PDFs, text files, and code documents
*   Automatic text extraction and processing
*   Knowledge base management with UUID-based organization
*   Automatic document monitoring and processing

### Knowledge Extraction

*   Named entity recognition (NER) with spaCy
*   Code pattern and programming concept identification
*   Topic detection and categorization
*   Personal information extraction (contact info, dates, education, etc.)

### Knowledge Graph

*   Relationship modeling between documents, topics, and concepts
*   Graph-based information retrieval
*   Entity and relationship visualization
*   Multiple knowledge base support

### Vector Search

*   Document embeddings using nomic-embed-text
*   Semantic similarity search
*   High-performance vector operations with Milvus
*   Configurable similarity measures (COSINE, etc.)

### Language Model Integration

*   Seamless integration with Ollama (llama3.1:8b)
*   Context-enhanced responses
*   Bilingual capabilities (English/Dutch)
*   Transparent proxy for LLM calls

### Web Interface

*   Open-source OpenWebUI integration
*   Document upload and management
*   Chat interface with knowledge-enhanced responses
*   Multiple knowledge base support

System Components
-----------------

JarvisAI consists of several interconnected components that work together to provide a complete RAG solution:

Component

Technology

Purpose

Language Model Server

Ollama with llama3.1:8b

Executes the large language model for generating responses

Web Interface

OpenWebUI

Provides user interface for chat, document upload, and management

Document Processor

Python, spaCy, PyPDF2

Extracts text and knowledge from documents

Graph Database

Neo4j

Stores knowledge graph with entities, topics, and relationships

Vector Database

Milvus

Stores document embeddings for semantic search

Ollama Proxy

Flask

Enhances LLM requests with hybrid search results

Metadata Storage

etcd

Stores metadata for Milvus

Object Storage

MinIO

Stores vector data for Milvus

Architecture
------------

JarvisAI follows a microservices architecture with containerized components that communicate with each other:

1.  **Document Flow**:
    *   User uploads documents through OpenWebUI
    *   Document Processor monitors for new files
    *   Processor extracts text, identifies entities, concepts, and relationships
    *   Knowledge is stored in Neo4j (graph database)
    *   Document embeddings are generated and stored in Milvus (vector database)
2.  **Query Flow**:
    *   User submits query through OpenWebUI
    *   Request is intercepted by Ollama Proxy
    *   Proxy performs hybrid search combining Neo4j and Milvus results
    *   Relevant context is extracted and added to the LLM prompt
    *   Enhanced prompt is sent to Ollama for processing
    *   Response is returned to user with relevant context

The hybrid search mechanism ensures that both semantic similarity (vector search) and relationship context (graph search) are considered when retrieving information, providing more comprehensive and relevant results than either approach alone.

Requirements
------------

JarvisAI has the following hardware and software requirements:

### Hardware Requirements

*   Two NVIDIA V100 GPUs (16GB each)
*   Dual Xeon CPUs
*   256GB RAM
*   10TB of storage

### Software Requirements

*   Linux-based operating system (Ubuntu 20.04 or newer recommended)
*   Docker and Docker Compose (v2.x+)
*   NVIDIA Container Toolkit (for GPU access in containers)
*   Git (for repository cloning)
*   Python 3.10 or newer (for the document processor)

Installation
------------

### Step 1: Clone the Repository

    git clone https://github.com/yourusername/jarvisai.git
    cd jarvisai

### Step 2: Set Up Environment Variables

### Automatic Installation

JarvisAI comes with an automated setup script (`start.sh`) that handles all installation steps for you:

    git clone https://github.com/AnubissBE/jarvisai.git
    cd jarvisai
    chmod +x start.sh
    ./start.sh

The script will:

*   Check system requirements
*   Install Docker and Docker Compose if needed
*   Set up NVIDIA Container Toolkit if GPU is available
*   Create necessary configuration files
*   Start all Docker containers
*   Set up the Jarvis model in Ollama
*   Configure OpenWebUI
*   Provide access information

**Warning:** Initial startup may take considerable time (30+ minutes) as models are downloaded and containers are initialized.

### Manual Installation

If you prefer to install manually, follow these steps:

#### Step 1: Clone the Repository

    git clone https://github.com/AnubissBE/jarvisai.git
    cd jarvisai

#### Step 2: Set Up Environment Variables

Create a secure secret key for the web interface:

    echo "WEBUI_SECRET_KEY=$(openssl rand -hex 32)" > .env

### Step 3: Build and Start the Containers

    docker-compose up -d

### Required Ollama Models

JarvisAI relies on two models from Ollama:

* `llama3.1:8b` – the base model used to build the custom **jarvis** model.
* `nomic-embed-text` – provides embeddings for hybrid search.

You can pull these models manually before starting the system:

```bash
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

The [`start.sh`](start.sh) script automatically pulls `llama3.1:8b` and `nomic-embed-text` when creating the `jarvis` model as shown in the script:
```
curl -X POST "http://localhost:11434/api/pull" \
    -H "Content-Type: application/json" \
    -d '{"name": "llama3.1:8b"}'
```
Model selection for embeddings is configured in [`docker-compose.yml`](docker-compose.yml):
```
EMBEDDING_MODEL=nomic-embed-text
```

**Warning:** Initial startup may take considerable time (30+ minutes) as models are downloaded and containers are initialized.

### Step 4: Verify Installation
#### Step 4: Create the Jarvis Model

Wait for Ollama to start, then create the Jarvis model:

    curl -X POST "http://localhost:11434/api/create" \
        -H "Content-Type: application/json" \
        -d "{\"name\": \"jarvis\", \"modelfile\": \"$(cat Modelfile | sed 's/"/\\"/g' | tr '\n' ' ')\"}"

#### Step 5: Verify Installation

Check if all services are running properly:

    docker-compose ps

Access the web interface at [http://localhost:3000](http://localhost:3000) and create an account. Default credentials are:

*   Username: `admin`
*   Password: `password` (change this immediately!)

Configuration
-------------

### System Configuration

The main system configuration is in `docker-compose.yml` and `jarvis_kb_config.env`. Key configuration options include:

#### Database Connection Settings

* `NEO4J_URI` – address of the Neo4j database
* `NEO4J_USER` / `NEO4J_PASSWORD` – credentials for Neo4j
* `MILVUS_HOST` / `MILVUS_PORT` – location of the Milvus vector store

#### Ollama Settings

* `OLLAMA_URL` – base URL for the Ollama API
*   `OLLAMA_NUM_PARALLEL`: Number of parallel requests allowed (default: 4)
*   `OLLAMA_MAX_LOADED_MODELS`: Maximum models to keep loaded (default: 2)
*   `OLLAMA_CONTEXT_LENGTH`: Maximum context length (default: 262144)

#### Vector Search Settings

*   `MILVUS_INDEX_TYPE`: Index type for vector search (default: HNSW)
*   `MILVUS_METRIC_TYPE`: Similarity metric type (default: COSINE)
*   `EMBEDDING_DIMENSIONS`: Dimensions of embeddings (default: 768)

#### Document Processing Settings

*   `ENABLE_KB_DISCOVERY`: Automatically discover knowledge bases (default: true)
*   `ENABLE_MULTI_KB_SEARCH`: Search across multiple knowledge bases (default: true)
*   `MAX_RESULTS_PER_KB`: Maximum results per knowledge base (default: 5)

### LLM Configuration

The LLM is configured in the `Modelfile`. You can modify this file to change LLM parameters:

    FROM llama3.1:8b
    
    SYSTEM """
    You are Jarvis, an advanced bilingual AI assistant fluent in both English and Dutch. 
    You automatically detect and respond in the language used by the user. 
    You have access to extended context through vector and graph databases, 
    enabling comprehensive knowledge retrieval and memory management.
    """
    PARAMETER num_ctx 131072
    PARAMETER num_gpu 2
    PARAMETER num_thread 24
    PARAMETER num_batch 512
    PARAMETER temperature 0.7
    PARAMETER top_k 40
    PARAMETER top_p 0.9
    PARAMETER repeat_penalty 1.1

    TEMPLATE """{{ if .System }}<|start_header_id|>system<|end_header_id|> {{ .System }} <|eot_id|>{{ end }}{{ if .Prompt }}<|start_header_id|>user<|end_header_id|> {{ .Prompt }} <|eot_id|>{{ end }}<|start_header_id|>assistant<|end_header_id|> {{ .Response }} <|eot_id|>"""

#### Optimizing for Dual V100 GPUs

For systems with two NVIDIA V100 GPUs and high core-count CPUs, adjust the following settings for best performance:

* `OLLAMA_NUM_THREADS=24` in `docker-compose.yml` to match the available CPU threads.
* `WEBUI_WORKERS=24` in `docker-compose.yml` for improved concurrency in the web interface.
* `num_thread 24` in the `Modelfile` to fully utilise the CPU when generating responses.

These values can be tweaked further depending on your exact workload and resource availability.

Usage
-----

### Web Interface

Access the web interface at [http://localhost:3000](http://localhost:3000) to interact with JarvisAI:

1.  Login with your credentials
2.  Create or select a knowledge base
3.  Upload documents to your knowledge base
4.  Chat with Jarvis, leveraging your knowledge base

### Uploading Documents

To add documents to your knowledge base:

1.  Click on the "Knowledge" tab in OpenWebUI
2.  Select your knowledge base or create a new one
3.  Click "Upload" and select your documents
4.  Wait for processing to complete (visible in the Knowledge tab)

Supported document types include:

*   PDF files (.pdf)
*   Text files (.txt, .md)
*   Code files (.py, .js, .html, .css, .java, .c, .cpp)
*   Other text-based documents (processed with pytextract)

### Interacting with JarvisAI

To chat with JarvisAI:

1.  Click on the "Chat" tab in OpenWebUI
2.  Select the appropriate model (typically llama3.1)
2.  Select the "jarvis" model from the dropdown
3.  Select your knowledge base from the dropdown
4.  Type your questions or commands

JarvisAI will automatically:

*   Analyze your query
*   Retrieve relevant information from your knowledge base
*   Enhance the LLM prompt with this information
*   Generate a response based on both the model and your knowledge

Document Processing
-------------------

The document processor is a key component that extracts knowledge from your documents. It performs several steps:

### Text Extraction

The system extracts text from various document formats:

*   PDF files: text extraction using PyPDF2
*   Text files: direct reading with appropriate encoding
*   Other formats: extraction using pytextract

### Technical Knowledge Extraction

The system identifies technical elements in documents:

*   Named entities (people, organizations, locations, etc.)
*   Programming topics (Python, JavaScript, Docker, etc.)
*   Code patterns and concepts (functions, classes, loops, etc.)
*   Relationships between topics and concepts

### Personal Knowledge Extraction

The system also identifies personal information:

*   Personal identifiers (names, contact information)
*   Temporal information (dates, deadlines)
*   Educational information (degrees, universities)
*   Professional information (jobs, skills)
*   Financial, health, relationship information
*   Projects, tasks, interests, and more

### Knowledge Graph Building

Extracted knowledge is organized in Neo4j as a knowledge graph with:

*   Document nodes linked to their source
*   Topic nodes representing subject areas
*   Concept nodes with descriptions and examples
*   Relationship edges connecting related entities
*   Personal entity nodes with categorized information

Knowledge Extraction
--------------------

The system uses a combination of techniques to extract knowledge:

### Entity Recognition

Using spaCy's named entity recognition to identify:

    entities = []
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "ORG", "GPE", "PRODUCT", "EVENT", "LAW", "WORK_OF_ART"]:
            entities.append({
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char
            })

### Topic Identification

Identifying topics through keyword matching:

    programming_topics = [
        "Python", "JavaScript", "Java", "C++", "Ruby", "Go", "Rust", 
        "Algorithm", "Data Structure", "API", "Framework", "Library",
        # ... more topics
    ]
    
    for topic in programming_topics:
        if re.search(r'\b' + re.escape(topic) + r'\b', text, re.IGNORECASE):
            topics.append(topic)

### Concept Extraction

Using regex patterns to identify programming concepts:

    concept_patterns = {
        "Function Definition": r'def\s+\w+\s*\(.*?\)\s*:',
        "Class Definition": r'class\s+\w+(\(.*?\))?\s*:',
        "Variable Assignment": r'\w+\s*=\s*[^=].*',
        # ... more patterns
    }

### Personal Information Extraction

Using specialized regex patterns for personal information:

    name_patterns = [
        r'(?i)name[\s:]+([A-Z][a-z]+(?: [A-Z][a-z]+)+)',
        r'(?i)I am ([A-Z][a-z]+(?: [A-Z][a-z]+)+)',
        r'(?i)(?:Mr|Mrs|Ms|Dr|Prof)\.?\s([A-Z][a-z]+(?: [A-Z][a-z]+)+)'
    ]
    
    contact_patterns = {
        "Email": r'[\w\.-]+@[\w\.-]+\.\w+',
        "Phone": r'(?:\+\d{1,3}[- ]?)?(?:\(\d{1,4}\)[- ]?)?\d{1,4}[- ]?\d{1,4}[- ]?\d{1,4}',
        # ... more patterns
    }

## Automated Start Script


JarvisAI includes a comprehensive `start.sh` script that automates the entire setup and launch process. This script performs the following functions:

### Script Features

*   System requirements check (CPU, RAM, disk space, GPU)
*   Docker and Docker Compose installation if not present
*   NVIDIA Container Toolkit setup for GPU support
*   Environment configuration (.env creation, directory setup)
*   Container build and launch
*   Jarvis model creation in Ollama
*   OpenWebUI configuration
*   Startup monitoring and status reporting

### Script Usage

Simply make the script executable and run it:

    chmod +x start.sh
    ./start.sh

The script will guide you through the entire process with clear, color-coded output.
You can also run the script with extra options:

    ./start.sh --logs    # View Docker container logs
    ./start.sh --debug   # Enable verbose output and display error codes


### CPU-Only Mode

If no NVIDIA GPU is detected, the script will automatically configure JarvisAI to run in CPU-only mode. This will be significantly slower than GPU mode but allows the system to run on machines without dedicated GPUs.

    
    # Excerpt from start.sh showing GPU detection logic
    if [ "$has_nvidia_gpu" = true ]; then
        echo -e "${GREEN}Starting with GPU support...${NC}"
        docker-compose up -d
    else
        echo -e "${YELLOW}Starting in CPU-only mode (performance will be limited)...${NC}"
        # Remove GPU-specific configurations when running without GPU
        sed 's/driver: nvidia/driver: none/g' docker-compose.yml > docker-compose-cpu.yml
        docker-compose -f docker-compose-cpu.yml up -d
    fi
    

Troubleshooting
---------------

### Common Issues

#### Docker Container Issues

If containers fail to start:

    docker-compose logs [service_name]

To restart a specific service:

    docker-compose restart [service_name]

#### GPU Access Issues

If containers can't access GPUs:

1.  Verify NVIDIA drivers are installed: `nvidia-smi`
2.  Check NVIDIA Container Toolkit: `docker run --gpus all nvidia/cuda:11.0-base nvidia-smi`

#### Document Processing Issues

If documents aren't being processed:

    docker-compose logs document-processor

Check the logs for specific errors related to file access, text extraction, or database connections.

#### Knowledge Base Issues

If knowledge base isn't showing or working properly:

1.  Check Neo4j database: `http://localhost:7474` (neo4j/hahanotmypassword)
2.  Verify document processor logs: `docker-compose logs document-processor`

### Resetting the System

To completely reset the system and start fresh:

    docker-compose down -v
    docker-compose up -d

**Warning:** This will delete all data, including knowledge bases, documents, and user accounts.

Security Notes
--------------

**Important Security Considerations:**

*   **Password Security**: The default passwords in the configuration files should be changed before deploying in a production environment.
*   **Exposed Ports**: By default, several services expose ports that should be properly secured if the system is accessible beyond your local network.
*   **Personal Data**: The system extracts and stores personal information from documents. Ensure compliance with privacy regulations if processing sensitive data.
*   **Network Isolation**: Consider using Docker network isolation to restrict external access to internal services.

### Securing Your Installation

Recommended security measures:

1.  Change default passwords in `docker-compose.yml` and `jarvis_kb_config.env`
2.  Enable HTTPS for exposed web interfaces
3.  Implement proper authentication for all services
4.  Regularly update all components and dependencies

Development
-----------

### Project Structure

    .
    ├── docker-compose.yml       # Main Docker Compose configuration
    ├── start.sh                 # Automated setup script
    ├── Dockerfile.document-processor # Dockerfile for document processor
    ├── document_processor.py    # Document processing code
    ├── hybrid_search/hybrid_search.py  # Hybrid search implementation
    ├── jarvis_kb_config.env     # Environment configuration
    ├── Modelfile                # Ollama model configuration
    ├── proxy/ollama_proxy.py    # Proxy for enhancing LLM requests
    ├── milvus.compose.yml       # Milvus vector database config
    └── proxy/                   # Proxy service code
        └── Dockerfile           # Dockerfile for proxy service

### Development Environment

To set up a development environment:

1.  Clone the repository
2.  Modify `docker-compose.yml` to mount local code directories
3.  Use `docker-compose up -d` to start the services
4.  Make code changes and restart affected services

### Contributing

Contributions are welcome! To contribute:

1.  Fork the repository
2.  Create a feature branch
3.  Make your changes
4.  Submit a pull request

### Extending the System

JarvisAI can be extended in several ways:

*   Adding support for additional document types
*   Enhancing knowledge extraction with custom patterns
*   Implementing additional search strategies
*   Integrating with other LLM providers
*   Adding visualization capabilities for the knowledge graph

Created by [AnubissBE](https://github.com/AnubissBE)
