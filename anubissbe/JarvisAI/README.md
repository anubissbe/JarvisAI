# JarvisAI - Your Personal AI Assistant

JarvisAI is a modern, full-stack AI assistant application that provides a conversational interface to help with various tasks. Built with Python FastAPI backend and React TypeScript frontend, it offers a seamless experience for interacting with AI.

## Features

- 🤖 Conversational AI powered by OpenAI's GPT models
- 🔊 Text-to-speech capabilities for natural interaction
- 🎛️ Customizable settings for voice, AI model, and appearance
- 🔌 Extensible integration system for third-party services
- 🔒 User authentication and personalized experiences
- 📱 Responsive design that works on desktop and mobile

## Architecture

JarvisAI follows a modern microservices architecture:

- **Backend**: Python FastAPI application providing RESTful API endpoints
- **Frontend**: React with TypeScript and Material-UI for a responsive interface
- **Database**: MongoDB for storing user data and settings
- **Authentication**: JWT-based authentication system
- **AI Integration**: OpenAI API for natural language processing

## Getting Started

### Prerequisites

- Docker and Docker Compose
- OpenAI API key

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/anubissbe/JarvisAI.git
   cd JarvisAI
   ```

2. Create a `.env` file in the root directory with the following variables:
   ```
   OPENAI_API_KEY=your_openai_api_key
   JWT_SECRET_KEY=your_jwt_secret_key
   ```

3. Start the application using Docker Compose:
   ```bash
   docker-compose up -d
   ```

4. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - MongoDB Express (database UI): http://localhost:8081

## Development

### Backend Development

The backend is built with FastAPI and follows a modular structure: