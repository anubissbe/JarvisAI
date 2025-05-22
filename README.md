# JarvisAI - Your Personal AI Assistant

JarvisAI is an advanced AI assistant inspired by Tony Stark's JARVIS from the Marvel universe. It's designed to help you with various tasks through natural language interaction, providing a seamless and intuitive user experience.

## How It Works

JarvisAI uses a combination of technologies to understand and respond to your commands:

1. **Speech Recognition**: Converts your spoken words into text using advanced speech-to-text algorithms
2. **Natural Language Processing**: Analyzes your text commands to understand your intent
3. **Task Execution**: Performs the requested action through various integrated modules
4. **Text-to-Speech**: Converts the response back into spoken words

The system is built with a modular architecture that allows for easy extension and customization of capabilities.

## Features

- **Natural Language Processing**: Communicate with JarvisAI using everyday language
- **Voice Recognition**: Speak to JarvisAI and get voice responses
- **Document Processing**: Upload documents to create a knowledge base for your assistant
- **Knowledge Graph**: Store and retrieve information in a structured way using Neo4j

## Technology Stack

- **Ollama**: Local Large Language Model serving
- **OpenWebUI**: Web interface for interacting with JarvisAI
- **Neo4j**: Graph database for knowledge storage
- **Flask**: Web framework for the speech service
- **Docker**: Containerization for easy deployment and management

## System Architecture

JarvisAI consists of several interconnected services:

1. **Ollama**: Serves the large language model
2. **Ollama Proxy**: Handles concurrent requests to the Ollama API
3. **OpenWebUI**: Provides a web interface for interacting with the model
4. **Document Processor**: Extracts text from documents and builds a knowledge base
5. **Speech Service**: Handles speech-to-text and text-to-speech conversion
6. **Neo4j**: Stores document information and relationships

## Installation

### Option 1: Using Docker (Recommended)

#### Prerequisites
- Docker and Docker Compose
- NVIDIA GPU (optional, for better performance)
- NVIDIA Container Toolkit (if using GPU)

#### Quick Start with Docker

1. **Clone the repository**:
   ```bash
   git clone https://github.com/anubissbe/JarvisAI.git
   cd JarvisAI
   ```

2. **Configure your API keys**:
   - Create a `.env` file in the root directory
   - Add your API keys following the example in `.env.example`

3. **Start JarvisAI using the start script**:
   ```bash
   ./start.sh
   ```

   This script will:
   - Build the Docker container if it doesn't exist
   - Start the JarvisAI service
   - Mount necessary volumes for persistence
   - Configure audio devices for voice interaction

4. **Stop JarvisAI**:
   ```bash
   docker-compose down
   ```

### Option 2: Manual Installation

#### Prerequisites
- Python 3.10 or higher
- Neo4j database
- Ollama

#### Step-by-Step Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/anubissbe/JarvisAI.git
   cd JarvisAI
   ```

2. **Create and activate a virtual environment** (recommended):
   ```bash
   # On Windows
   python -m venv venv
   venv\Scripts\activate

   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install additional system dependencies**:

   For speech recognition:
   ```bash
   # On Ubuntu/Debian
   sudo apt-get install portaudio19-dev python-pyaudio python3-pyaudio

   # On macOS
   brew install portaudio

   # On Windows
   # No additional steps required
   ```

5. **Configure your API keys**:
   - Create a `.env` file in the root directory
   - Add your API keys following this format:
     ```
     NEO4J_PASSWORD=your_neo4j_password_here
     WEBUI_SECRET_KEY=your_secret_key_here
     # Add other API keys as needed
     ```

## Usage

### Starting JarvisAI

#### With Docker

Simply run:
```bash
./start.sh
```

#### With Manual Installation

1. **Activate your virtual environment** (if you created one):
   ```bash
   # On Windows
   venv\Scripts\activate

   # On macOS/Linux
   source venv/bin/activate
   ```

2. **Run the main script**:
   ```bash
   python main.py
   ```

### Web Interface

Access the web interface at:
```
http://localhost:3000
```

### Voice Commands

JarvisAI responds to voice commands when activated with the wake word "Hey Jarvis" or "Hello Jarvis".

### Text-Based Interaction

If you prefer typing commands instead of speaking:

1. Run the program with the `--text-only` flag:
   ```bash
   python main.py --text-only
   ```

2. Type your commands in the console when prompted

## Document Processing

JarvisAI can process documents to build a knowledge base:

1. Place documents in the `uploads` folder
2. JarvisAI will automatically process them and extract information
3. Documents are stored in Neo4j for efficient retrieval
4. Supported formats: PDF, DOCX, TXT, HTML, CSV, etc.

## Customization

### Configuration Files

JarvisAI can be customized by modifying these configuration files:

  ```json
  {
    "assistant_name": "Jarvis",
    "voice_id": "en-US-Standard-D",
    "wake_word": "Hey Jarvis",
    "language": "en-US",
    "volume": 1.0,
    "speech_rate": 1.0
  }
  ```

### Modelfile

You can customize the Jarvis LLM by modifying the `Modelfile`:

```
FROM llama3.1:8b

SYSTEM """
You are Jarvis, an advanced AI assistant inspired by Tony Stark's JARVIS...
"""

PARAMETER temperature 0.7
...
```

## Testing

JarvisAI includes a comprehensive test suite:

```bash
# Run all tests
python run_tests.py

# Run specific test module
python run_tests.py --module tests.test_ollama_proxy

# Run integration test
python run_tests.py --integration
```

## Troubleshooting

### Common Issues

1. **Microphone not working**:
   - Check if your microphone is properly connected
   - Ensure you've granted microphone permissions to the application
   - Try running: `python -m speech_recognition` to test your microphone

2. **Speech recognition errors**:
   - Speak clearly and in a quiet environment
   - Check your internet connection (some speech recognition services require internet)
   - Try adjusting the microphone sensitivity in your system settings

3. **API key issues**:
   - Verify that your API keys are correctly set in the `.env` file
   - Check if your API keys are still valid and have sufficient quota

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

Project Link: [https://github.com/anubissbe/JarvisAI](https://github.com/anubissbe/JarvisAI)

Made with ❤️ by [anubissbe](https://github.com/anubissbe)